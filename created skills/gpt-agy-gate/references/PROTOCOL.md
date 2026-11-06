# Codex ↔ Antigravity Live PM Protocol

Ba file trong `.antigravity/agy-bridge/`:

- `PROTOCOL.md`: quy tắc duy nhất của bridge.
- `bridge.py`: chuyển đúng một lượt task cho Antigravity.
- `chat.md`: mailbox và nhật ký hội thoại.

## Vai trò

- User giao mục tiêu cho Codex trong cửa sổ chat.
- Codex live là PM và auditor duy nhất.
- Antigravity là implementer, chỉ sửa file trong phạm vi task.
- Bridge chỉ chuyển task và ghi response; không gọi Codex CLI, không tự audit, không tự approve, không chạy nền.

## Quy trình bắt buộc

1. Codex đọc AGENTS.md, skill và file liên quan.
2. Codex ghi task packet `status=queued` vào `chat.md`, gồm `task_id`, scope, acceptance criteria, quality gates, `MAX_ROUNDS` và `do_not_change`.
3. Codex chạy `python3 .antigravity/agy-bridge/bridge.py` đúng một lần.
4. Bridge gọi `agy` một lượt, ghi `Antigravity → Codex` và chuyển task sang `waiting-review`.
5. Codex live chờ response, đọc diff/file thật, chạy kiểm tra cần thiết.
6. Nếu chưa đạt, Codex ghi một revision assignment mới vào `chat.md`, tăng round và chạy bridge một lần nữa.
7. Nếu đạt, Codex chuyển task sang `approved` và báo cáo User.
8. Nếu User bảo dừng, Codex dừng process, chuyển task sang `stopped` và không tự chạy lại.

### Live loop tự động sau audit

- `bridge.py --once` chỉ thực hiện một round; không được hiểu là toàn bộ task đã kết thúc.
- Trong cùng một live turn, sau khi Antigravity trả response, Codex phải audit diff/file thật. Nếu acceptance criteria chưa đạt và vẫn còn round, Codex tự tạo revision assignment, cập nhật round và tự gọi lại `python3 .antigravity/agy-bridge/bridge.py --once` mà không cần User xác nhận.
- Quy trình tự lặp là: dispatch → chờ response → audit → revision nếu fail → dispatch lại. Chỉ kết thúc khi task `approved`, User yêu cầu dừng, có blocker thật cần User quyết định, hoặc đã chạm `MAX_ROUNDS`.
- `MAX_ROUNDS` là giới hạn tối đa cho toàn bộ live loop, không phải số vòng tối thiểu. Không được dừng sớm chỉ vì một round đã trả response nếu task vẫn chưa đạt và còn quota.
- Nếu chạm `MAX_ROUNDS` mà chưa đạt, chuyển task sang `stopped`, ghi `MAX_ROUNDS_EXHAUSTED`, rồi mới báo User.

### Kế thừa và thay đổi giới hạn vòng

- Nếu User không nêu `MAX_ROUNDS` mới, Codex phải kế thừa giới hạn đang có hiệu lực cho task/workflow hiện tại; không tự đặt lại hoặc dùng một giá trị khác.
- Nếu User nêu `MAX_ROUNDS` mới, Codex phải cập nhật con số đó trong task packet và mọi assignment/revision record liên quan trước khi dispatch bridge.
- Bridge chỉ được chạy sau khi packet đã chứa giới hạn cuối cùng. Không để prompt dispatch, packet và log cùng task ghi các giới hạn khác nhau.
- Khi audit, Codex phải dùng đúng giới hạn đã ghi trong packet active; không tính các giá trị cũ trong log lịch sử là vòng mới.
- Một task chỉ có duy nhất một giá trị `MAX_ROUNDS` có hiệu lực. Giá trị đó phải nhất quán trong task packet, mọi revision assignment, prompt dispatch, bridge/runtime record và mọi file code hoặc file cấu hình tham gia điều phối task. Không được để packet ghi một limit nhưng code, prompt hoặc revision dùng limit khác.
- Trước mỗi dispatch và trước mỗi revision, Codex phải kiểm tra sự nhất quán của limit giữa các thành phần liên quan. Nếu phát hiện lệch, phải sửa về giá trị đã được User đặt rồi mới chạy tiếp; không được âm thầm chọn giá trị thấp hơn hoặc cao hơn.
- Các task khác nhau có thể có `MAX_ROUNDS` khác nhau; không được lấy limit của task trước áp dụng sang task mới. Lịch sử cũ chỉ để tham chiếu, không có hiệu lực runtime.

### Live response handoff và quota

- Bridge là process đồng bộ: Codex mở một lượt bridge và chờ process đó kết thúc. Không dùng polling `chat.md` trong khi Antigravity đang chạy.
- **Quy tắc chờ live tuyệt đối:** Trong một bridge cycle đang chạy, Codex chỉ giữ live session để chờ process bàn giao. Cấm đọc lại `chat.md`, kiểm tra diff/file, gọi status, spawn thêm bridge hoặc lặp các lệnh kiểm tra giữa chừng. Chỉ khi bridge process đã kết thúc và ghi response thì Codex mới được bắt đầu audit. Việc chờ bằng chính session/process là hợp lệ; polling mailbox không hợp lệ.
- Chỉ coi lượt làm việc đã sẵn sàng audit khi bridge đã ghi block `Antigravity → Codex` vào `chat.md` và trả control về Codex. Response đó là tín hiệu bàn giao; không cần kiểm tra mailbox định kỳ.
- Sau tín hiệu bàn giao, Codex chỉ đọc response, diff/file vừa sửa và các test gộp hoặc risk sample cần thiết. Không đọc lại toàn bộ workspace nếu phần đó không đổi.
- Nếu bridge process chết, timeout hoặc không ghi response, Codex được phép kiểm tra một lần để chẩn đoán launcher failure; không tự dispatch lặp vô hạn.
- Quy tắc này giảm lượt đọc và quota, nhưng không biến mailbox thành daemon và không đảm bảo đánh thức một Codex session đã kết thúc. Muốn cycle tiếp tục, phiên Codex live phải còn mở hoặc phải được mở lại.
- Sau khi đã dispatch task, Codex không được gửi `final`, không được kết thúc lượt và không được báo “đang chờ” như một kết luận tạm thời. Codex phải giữ live turn, chờ bridge trả response, audit và tự dispatch revision tiếp theo nếu cần.
- Chỉ được kết thúc live turn khi task đã `approved`, đã `stopped` vì chạm `MAX_ROUNDS`, User yêu cầu dừng, hoặc có blocker thật cần User quyết định. Khi kết thúc phải báo trạng thái terminal chính xác.

## Lifecycle

`queued → running → waiting-review → queued → running → waiting-review → approved`

Nhánh lỗi: `running → rejected`.

Không dùng `AUTOPILOT` để biến bridge thành PM nền. `MAX_ROUNDS` là giới hạn mà Codex live phải tự đếm; khi chạm giới hạn mà chưa đạt, chuyển `stopped` và ghi `MAX_ROUNDS_EXHAUSTED`.

## Hội thoại bắt buộc trong chat.md

- `Codex → Antigravity`: task assignment hoặc revision assignment.
- `Antigravity → Codex`: implementation response.
- Codex không được chuyển `approved` dựa trên báo cáo của Antigravity mà chưa kiểm tra diff/file thật.
- Antigravity không được tự approve, tự commit, tự push, tự xóa, đổi tên hoặc mở rộng scope.

## Quy tắc dừng

- Không có process bridge hoặc Antigravity nào được giữ chạy sau khi task kết thúc.
- Không có Codex CLI PM nền.
- Khi lượt chat của Codex kết thúc, cycle live kết thúc; mailbox không được coi là cơ chế đánh thức lại Codex.
- Task terminal (`approved`, `rejected`, `stopped`) không được tự chạy lại.

## Default tiết kiệm quota cho mọi task

Trừ khi User yêu cầu khác, Codex và Antigravity phải dùng chiến lược dưới đây cho mọi task, không chỉ workspace này.

### 1. Một spec hoàn chỉnh, không chia task vụn

- Codex phải giao một task packet tổng trước khi chạy agent: objective, scope, việc cấm, Definition of Done, test bắt buộc, format report và `MAX_ROUNDS`.
- Agent phải tự phân rã công việc nội bộ; không trả plan-only hoặc audit-only khi task có thể triển khai được.
- Default `MAX_ROUNDS: 2`: một lượt implementation toàn scope và tối đa một lượt revision tổng. Khi User đặt limit khác, live loop phải dùng đúng limit đó và tự chạy tiếp qua các revision cần thiết cho đến khi đạt hoặc hết limit. Không tạo revision theo module/chức năng nhỏ nếu chưa có lỗi đo được.
- Mỗi task chỉ có một packet `queued` active. Revision phải là packet mới độc lập có `<!-- END TASK -->`; không nhét revision vào lịch sử chat của packet cũ.

### 2. Chọn agent và model theo độ khó

- Việc cơ học, inventory, format, link scan, lint và migration rõ: dùng model nhẹ khi có.
- Debug, refactor và feature thông thường: dùng model workhorse.
- Kiến trúc, security, dữ liệu chuyên môn có rủi ro cao, nghiên cứu hoặc nội dung giáo trình: dùng model mạnh; không dùng model nhẹ để bịa kiến thức.
- Nếu task lớn có các vùng file độc lập, Codex có thể giao song song; mỗi agent phải sở hữu một vùng file không chồng lấp. Không cho nhiều agent cùng sửa shared CSS, config, lockfile, mailbox hoặc một file.

### 3. Agent tự kiểm tra trước khi báo

- Agent phải sửa file thật, tự chạy test phù hợp rồi mới trả response.
- Agent không được trả lời bằng lời chào, nhắc lại yêu cầu, kế hoạch dài, chain-of-thought hoặc liệt kê mọi file đã đọc nếu không cần để debug.
- Báo cáo mặc định chỉ gồm:
  - `Changed`: file và thay đổi thực.
  - `Verified`: test và kết quả có số liệu.
  - `Remaining`: lỗi/blocker còn lại, hoặc `none`.
  - `Decision`: chỉ ghi khi Codex/User thật sự phải chọn.

### 4. Audit tối thiểu nhưng đủ tin

Codex không được đọc mọi file chỉ để yên tâm. Audit theo ba lớp:

- Machine checks: build/test/lint/parser/type check/link-anchor-asset scan/secret-or-placeholder scan tùy task.
- Diff and scope check: xác nhận file đổi đúng scope, không có placeholder, hard-code hoặc copy-paste rõ ràng.
- Risk sample: chỉ đọc sâu file đầu/cuối, luồng quan trọng, logic phức tạp hoặc phần User báo lỗi.

Chỉ tạo revision khi test fail, Definition of Done chưa đạt, report mâu thuẫn file thật, agent không sửa, vượt scope, hoặc User thấy lỗi. Pass thì approve ngay, không cố dùng hết rounds.

### 5. Quản lý mailbox và bridge

- Bridge luôn dispatch packet `queued` mới nhất có `<!-- END TASK -->`; không replay packet lịch sử.
- Codex phải chuyển packet cũ sang terminal trước khi tạo task thay thế.
- Không dùng polling/diff liên tục khi agent đang chạy. Chỉ kiểm tra một lần khi agent phản hồi, trừ khi User yêu cầu status.
- Không tạo Codex CLI PM, background watcher hoặc agent nền; live Codex là PM duy nhất.

### 6. Template ngắn User giao Codex

```text
Làm [mục tiêu].

Phạm vi: [folder/file/system].
Cấm: [xóa/rename/commit/push hoặc giới hạn khác].
Chất lượng: [tiêu chí].
Tự giao Antigravity làm toàn bộ một lần, dùng subagent nội bộ nếu cần.
Tối đa 2 vòng: implementation + revision.
Mày chỉ audit bằng test gộp, diff và sample rủi ro.
Không chat kế hoạch, không audit-only, không chia task lẻ.
Xong mới báo tao.
```

### 7. Format Spec chuẩn Codex giao Antigravity

```text
<!-- TASK id=<unique-id> status=queued from=codex -->
AUTOPILOT: false
MAX_ROUNDS: 2

Objective:
[Outcome cuối]

Scope:
[File/thư mục/hệ thống]

Do:
[Các việc phải làm]

Do not:
[Không rename/delete/commit/push...]

Definition of Done:
[Điều kiện pass đo được]

Verification:
[Test cụ thể]

Execution:
- Tự chia việc nội bộ nếu cần.
- Không gửi báo cáo giữa chừng.
- Không trả plan-only/audit-only.
- Chỉ trả khi hoàn thành tối đa scope hoặc có blocker thực tế.

Report only:
- Changed: [file: thay đổi]
- Verified: [test: result]
- Remaining: [none / blocker]
- Decision: [none / cần chọn X]

<!-- END TASK -->
```
