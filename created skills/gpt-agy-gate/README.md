# My Skills

Repository lưu trữ và thử nghiệm các custom AI agent skills (Antigravity, Codex, và các công cụ liên quan).

## Skills

### `create-gpt-agy-gate`
Quy trình phối hợp kiểm soát chất lượng giữa Codex PM và Antigravity CLI cho các task triển khai, tái cấu trúc, kiểm thử và tài liệu hóa.
- **Tiêu chí cốt lõi:** Phân vai rõ ràng (Codex PM/Auditor vs Antigravity Implementer), luồng rẻ nhất 1 lượt thực thi chính + tối đa 1 lượt revision, kiểm tra 3 lớp (Máy, Diff, Risk Sample) và báo cáo tối ưu token.
- **Tài liệu tham chiếu:**
  - `references/task-packet-template.md`: Mẫu task packet chuẩn hóa giao việc.
  - `references/audit-checklist.md`: Danh mục kiểm tra nghiệm thu.
  - `references/bridge-contract.md`: Hợp đồng vòng đời bridge một lượt.
  - `references/quota-optimization.md`: Hướng dẫn chi tiết về phân bổ model, số lượng agent và tối ưu quota.

## License
MIT License - Xem chi tiết tại [LICENSE](LICENSE).
