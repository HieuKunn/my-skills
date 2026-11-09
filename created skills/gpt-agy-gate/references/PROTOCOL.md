# Codex ↔ Antigravity Bridge Protocol

## Phạm vi

Bridge dùng đúng ba file:

- `bridge.py`: điều phối một attempt.
- `chat.md`: mailbox, packet và response.
- `PROTOCOL.md`: luật vận hành.

Bridge không dùng `tasks/`, `schema/`, `templates/`, `defaults.json`, `spec.md`, `state.json` hoặc `history.jsonl`.

## Phân vai

- User giao mục tiêu, phạm vi, chất lượng và giới hạn riêng của task.
- Codex là PM, viết packet, điều phối, audit diff/file/test và quyết định verdict.
- Antigravity là implementer, tự sửa trong scope, tự kiểm tra và báo cáo.
- Bridge chỉ khóa mailbox, kiểm tra packet, gọi một attempt, ghi response và chuyển trạng thái.

Antigravity không được tự approve. Bridge không được tự audit hoặc approve.

## Mailbox và FIFO

`chat.md` chỉ giữ tối đa 3 task stream gần nhất. Một task stream gồm task gốc và mọi revision của nó. Revision không chiếm slot riêng.

Khi thêm task gốc thứ tư, bridge xóa toàn bộ stream cũ nhất theo thời điểm `created`. Đây là FIFO và là hành vi xóa lịch sử khỏi mailbox theo yêu cầu. Bridge xóa cả packet và các message của stream đó.

Khi có hơn 3 stream, bridge phải áp dụng FIFO trước rồi mới validate mailbox còn lại. Bridge phải từ chối task ID sai, revision sai parent, ROUND trùng hoặc revision không tăng dần trong các packet mới.

## Packet bắt buộc

```text
<!-- TASK id=TASK-001 status=queued created=2026-11-09T16:00:00+08:00 -->
TASK_VERSION: 1
PARENT_TASK: none
ROUND: 1
MAX_ROUNDS: 2
TIMEOUT_SECONDS: 7200
MAX_SUBAGENT_CALLS: 0
MAX_PARALLEL_AGENTS: 1
ACCEPTANCE_MODE: delegated

Objective:
...

Context:
...

Scope:
...

Do:
...

Do not:
...

Definition of Done:
...

Verification:
...

Agent policy:
...

Report format:
Changed:
Verified:
Evidence:
Remaining:
Decision:
<!-- END TASK -->
```

`MAX_ROUNDS` là tổng số attempt của Antigravity chính. `MAX_SUBAGENT_CALLS` và `MAX_PARALLEL_AGENTS` là giới hạn riêng cho agent con. Task mới không kế thừa limit task cũ.

## Context và quota

Bridge không nhúng toàn bộ `AGENTS.md` hoặc `PROTOCOL.md` vào prompt. Prompt phải yêu cầu Antigravity đọc trực tiếp hai file đó từ workspace, kèm đường dẫn rõ ràng.

Bridge chỉ truyền:

- packet task đầy đủ;
- limit của task;
- agent policy;
- revision hiện hành;
- các luật áp dụng trực tiếp cho task.

Hash file luật có thể được ghi trong response để truy nguyên phiên bản. Hash không chứng minh mô hình hiểu hoàn toàn nội dung; Codex vẫn phải kiểm tra kết quả thật.

## Agent policy

Mỗi attempt mặc định có một Antigravity chính. Antigravity chỉ được gọi subagent khi packet cho phép. Subagent không được mở rộng scope, sửa file dùng chung trái phép hoặc approve.

Codex chỉ chạy nhiều Antigravity song song khi mỗi agent có scope không chồng lấn. Không chạy song song khi cùng sửa `bridge.py`, `PROTOCOL.md`, `AGENTS.md`, `chat.md` hoặc file dùng chung.

## Lifecycle

```text
queued → running → waiting-review → approved
                         ├────────→ verified
                         ├────────→ rejected → queued
                         ├────────→ blocked
                         └────────→ stopped
```

- Chỉ packet `queued` được dispatch.
- `waiting-review`, `rejected`, `verified`, `approved` và `stopped` không tự replay.
- `MAX_ROUNDS` hết trước khi đạt thì chuyển `stopped` với lý do `MAX_ROUNDS_EXHAUSTED`.
- Timeout hoặc lỗi môi trường chuyển `blocked`.
- `delegated` cho phép Codex approve sau audit.
- `user_required` chỉ cho Codex ghi `verified`; User phải chấp nhận để thành `approved`.

`bridge.py --once` chỉ gọi đúng một attempt. Nó không chạy toàn bộ vòng audit và revision.

## Audit của Codex

Codex kiểm tra ba lớp:

- Machine checks: command, exit code, test output và artifact.
- Diff/scope: file đổi thật, đúng phạm vi, không placeholder, không sửa trái luật.
- Risk sample: đọc sâu các file và logic có rủi ro.

CLI return code 0 chỉ chứng minh transport thành công. Nó không chứng minh task đạt. Response JSON lỗi, response rỗng hoặc thiếu report đều bị đánh dấu `rejected`.

## Report bắt buộc

Antigravity chỉ trả:

```text
Changed:
- File và thay đổi cụ thể.

Verified:
- Lệnh đã chạy, kết quả và exit code.

Evidence:
- Artifact hoặc output chứng minh.

Remaining:
- none hoặc blocker cụ thể.

Decision:
- none hoặc quyết định cần Codex/User.
```

Codex phải reject khi report mâu thuẫn diff, không có verification, evidence không tồn tại, hoặc Anti tự tuyên bố approve.

## Lock và stop condition

Bridge dùng một lock hệ điều hành để ngăn hai process cùng sửa `chat.md`. Khi lock đang bị giữ, process mới dừng ngay.

Bridge dừng task khi hết limit, timeout, lỗi transport, packet sai hoặc không có task `queued`. Không có bridge nền và không có Codex PM nền.

## FIFO và dữ liệu cũ

Task bị FIFO loại khỏi `chat.md` không được bridge gọi lại. Nếu cần giữ lâu dài, Codex phải đưa nội dung sang một file tài liệu riêng trước khi task bị loại. Bridge không tự tạo archive.
