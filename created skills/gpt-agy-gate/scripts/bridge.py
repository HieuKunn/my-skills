#!/usr/bin/env python3
"""Codex to Antigravity mailbox bridge; one dispatch attempt only."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
BRIDGE_DIR = Path(__file__).resolve().parent
CHAT = BRIDGE_DIR / "chat.md"
LOCK = BRIDGE_DIR / ".bridge.lock"
MAX_TASK_STREAMS = 3
STATUSES = {"queued", "running", "waiting-review", "rejected", "verified", "approved", "blocked", "stopped"}
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
TASK_RE = re.compile(
    r"(?ms)^<!-- TASK id=(?P<id>[^ ]+) status=(?P<status>[^ ]+)(?: created=(?P<created>[^ ]+))?[^>]* -->\n"
    r"(?P<body>.*?)^<!-- END TASK -->"
)
MESSAGE_RE = re.compile(r"(?ms)^## Message (?P<id>[^ ]+) — .*?\n.*?(?=^## Message |\Z)")


class BridgeError(RuntimeError):
    pass


class Lock:
    def __enter__(self):
        self.fd = os.open(LOCK, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(self.fd)
            raise BridgeError("Một bridge process khác đang chạy.") from exc
        return self

    def __exit__(self, exc_type, exc, tb):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        os.close(self.fd)


def read_chat() -> str:
    if not CHAT.is_file():
        raise BridgeError(f"Không tìm thấy mailbox: {CHAT}")
    return CHAT.read_text(encoding="utf-8")


def write_chat(value: str) -> None:
    temp = CHAT.with_name(f".{CHAT.name}.tmp.{os.getpid()}")
    temp.write_text(value, encoding="utf-8")
    os.replace(temp, CHAT)


def parse_fields(body: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in body.splitlines():
        match = re.match(r"^([A-Z][A-Z0-9_]*)\s*:\s*(.*?)\s*$", line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def root_id(task_id: str, fields: Dict[str, str]) -> str:
    parent = fields.get("PARENT_TASK", "none")
    return parent if parent != "none" else re.sub(r"-R\d+$", "", task_id)


def get_blocks(text: Optional[str] = None) -> List[re.Match[str]]:
    return list(TASK_RE.finditer(read_chat() if text is None else text))


def validate_block(match: re.Match[str]) -> Dict[str, str]:
    task_id = match.group("id")
    status = match.group("status")
    fields = parse_fields(match.group("body"))
    if not TASK_ID_RE.fullmatch(task_id):
        raise BridgeError(f"task_id không hợp lệ: {task_id}")
    if status not in STATUSES:
        raise BridgeError(f"status không hợp lệ cho {task_id}: {status}")
    is_current = "TASK_VERSION" in fields
    if is_current:
        required = (
            "TASK_VERSION", "PARENT_TASK", "ROUND", "MAX_ROUNDS", "TIMEOUT_SECONDS",
            "MAX_SUBAGENT_CALLS", "MAX_PARALLEL_AGENTS", "ACCEPTANCE_MODE",
        )
        missing = [field for field in required if not fields.get(field)]
        if missing:
            raise BridgeError(f"{task_id} thiếu field: {', '.join(missing)}")
    # Historical packets predate the current metadata. They remain readable.
    fields.setdefault("ROUND", re.search(r"-R(\d+)$", task_id).group(1) if re.search(r"-R(\d+)$", task_id) else "1")
    fields.setdefault("MAX_ROUNDS", "2")
    fields.setdefault("TIMEOUT_SECONDS", "7200")
    fields.setdefault("MAX_SUBAGENT_CALLS", "0")
    fields.setdefault("MAX_PARALLEL_AGENTS", "1")
    fields.setdefault("ACCEPTANCE_MODE", "delegated")
    for field in ("ROUND", "MAX_ROUNDS", "TIMEOUT_SECONDS"):
        if not fields[field].isdigit() or int(fields[field]) <= 0:
            raise BridgeError(f"{task_id} có {field} không phải số nguyên dương")
    if int(fields["ROUND"]) > int(fields["MAX_ROUNDS"]):
        raise BridgeError(f"{task_id} vượt MAX_ROUNDS")
    for field in ("MAX_SUBAGENT_CALLS", "MAX_PARALLEL_AGENTS"):
        if not fields[field].isdigit() or int(fields[field]) < 0 or (field == "MAX_PARALLEL_AGENTS" and int(fields[field]) == 0):
            raise BridgeError(f"{task_id} có {field} không hợp lệ")
    if fields["ACCEPTANCE_MODE"] not in ("delegated", "user_required"):
        raise BridgeError(f"{task_id} có ACCEPTANCE_MODE không hợp lệ")
    parent = fields.get("PARENT_TASK", "none")
    revision = re.search(r"-R(\d+)$", task_id)
    if is_current and revision and parent == "none":
        raise BridgeError(f"Revision {task_id} phải có PARENT_TASK")
    if is_current and parent != "none" and not TASK_ID_RE.fullmatch(parent):
        raise BridgeError(f"PARENT_TASK không hợp lệ trong {task_id}")
    return fields


def validate_mailbox(text: Optional[str] = None) -> Tuple[List[re.Match[str]], Dict[str, List[re.Match[str]]]]:
    found = get_blocks(text)
    grouped: Dict[str, List[re.Match[str]]] = {}
    for match in found:
        fields = validate_block(match)
        grouped.setdefault(root_id(match.group("id"), fields), []).append(match)
    for task_root, entries in grouped.items():
        if all("TASK_VERSION" not in parse_fields(entry.group("body")) for entry in entries):
            continue
        rounds = [int(validate_block(entry)["ROUND"]) for entry in entries]
        if len(rounds) != len(set(rounds)):
            raise BridgeError(f"{task_root} có ROUND trùng")
        if rounds != sorted(rounds):
            raise BridgeError(f"{task_root} có revision không theo thứ tự ROUND")
    return found, grouped


def prune_fifo(text: str) -> str:
    found, grouped = validate_mailbox(text)
    if len(grouped) <= MAX_TASK_STREAMS:
        return text
    ordered = sorted(
        grouped.items(),
        key=lambda item: min(m.group("created") or f"{m.start():020d}" for m in item[1]),
    )
    remove_roots = {root for root, _ in ordered[:-MAX_TASK_STREAMS]}
    kept = text
    for match in reversed(found):
        fields = parse_fields(match.group("body"))
        if root_id(match.group("id"), fields) in remove_roots:
            kept = kept[:match.start()] + kept[match.end():]
    keep_roots = set(grouped) - remove_roots
    def drop_message(match: re.Match[str]) -> str:
        rid = re.sub(r"-R\d+$", "", match.group("id"))
        return "" if rid not in keep_roots else match.group(0)
    return MESSAGE_RE.sub(drop_message, kept)


def replace_status(text: str, task_id: str, status: str) -> str:
    pattern = re.compile(rf"(<!-- TASK id={re.escape(task_id)} status=)[^ ]+([^>]*-->)")
    updated, count = pattern.subn(rf"\g<1>{status}\g<2>", text, count=1)
    if count != 1:
        raise BridgeError(f"Không tìm thấy packet {task_id}")
    return updated


def append_message(text: str, task_id: str, sender: str, recipient: str, kind: str, content: str) -> str:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S %z")
    return text + f"\n\n## Message {task_id} — {sender} → {recipient}\n- Time: {stamp}\n- Type: {kind}\n\n{content.rstrip()}\n"


def make_prompt(match: re.Match[str], fields: Dict[str, str]) -> str:
    return f"""Read AGENTS.md and .antigravity/agy-bridge/PROTOCOL.md from the workspace before editing.
Task ID: {match.group('id')}
Attempt: {fields['ROUND']} of {fields['MAX_ROUNDS']}
Timeout: {fields['TIMEOUT_SECONDS']} seconds
Do not self-approve or edit outside scope. Obey the packet's subagent policy.

TASK PACKET:
{match.group('body').strip()}

Return only:
Changed:
Verified:
Evidence:
Remaining:
Decision:
"""


def dispatch(task_id: Optional[str], dry_run: bool) -> int:
    with Lock():
        original = read_chat()
        text = prune_fifo(original)
        if text != original:
            write_chat(text)
        found, _ = validate_mailbox(text)
        candidates = [m for m in found if m.group("status") == "queued" and (task_id is None or m.group("id") == task_id)]
        if not candidates:
            raise BridgeError("Không có task queued phù hợp để dispatch.")
        match = candidates[-1]
        fields = validate_block(match)
        prompt = make_prompt(match, fields)
        if dry_run:
            print(prompt)
            return 0
        text = replace_status(text, match.group("id"), "running")
        write_chat(text)
        command = ["agy", "--output-format", "json", "--mode", "accept-edits", "--add-dir", str(ROOT), f"--print={prompt}"]
        try:
            process = subprocess.Popen(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=int(fields["TIMEOUT_SECONDS"]))
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=5)
                return_code = 124
        except Exception as exc:
            stdout, stderr, return_code = "", repr(exc), 1
        parsed = None
        try:
            parsed = json.loads(stdout.strip()) if stdout.strip() else None
        except json.JSONDecodeError:
            pass
        transport_ok = bool(return_code == 0 and isinstance(parsed, dict) and parsed.get("status") == "SUCCESS" and isinstance(parsed.get("response"), str) and parsed["response"].strip())
        status = "waiting-review" if transport_ok else ("blocked" if return_code == 124 else "rejected")
        content = f"Return code: {return_code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n\nTransport status: {'success' if transport_ok else 'failed'}"
        text = replace_status(text, match.group("id"), status)
        text = append_message(text, match.group("id"), "Antigravity", "Codex", "implementation response", content)
        write_chat(prune_fifo(text))
        print(f"{match.group('id')}: {status}; return_code={return_code}")
        return 0 if transport_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Mailbox bridge; one Antigravity dispatch attempt only.")
    parser.add_argument("--once", action="store_true", help="Run exactly one queued attempt")
    parser.add_argument("--task", help="Task ID to dispatch")
    parser.add_argument("--dry-run", action="store_true", help="Render prompt without calling Antigravity")
    parser.add_argument("--validate", action="store_true", help="Validate mailbox and apply FIFO pruning")
    args = parser.parse_args()
    try:
        if args.validate:
            with Lock():
                original = read_chat()
                cleaned = prune_fifo(original)
                if cleaned != original:
                    write_chat(cleaned)
                validate_mailbox(cleaned)
                print("Mailbox hợp lệ; tối đa 3 task stream.")
            return 0
        if args.once or args.task:
            return dispatch(args.task, args.dry_run)
        parser.print_help()
        return 0
    except BridgeError as exc:
        print(f"Bridge error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
