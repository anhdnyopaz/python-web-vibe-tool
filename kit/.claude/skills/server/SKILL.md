---
name: server
description: Vận hành bản đang chạy thật — xem trạng thái, xem log, backup ngay, liệt kê backup, quay lại phiên bản trước, khôi phục dữ liệu. Dùng khi người dùng hỏi về server/bản online hoặc gõ /server.
argument-hint: "[status | logs | backup | backups | rollback | restore]"
---

# /server — Vận hành bản chạy thật

Thao tác: $ARGUMENTS (để trống thì `status`). Đọc bảng "Vận hành" trong `.claude/skills/deploy-playbook/SKILL.md` và dùng `.deploy/config` để biết VPS hay tunnel.

| Thao tác | Việc làm | Báo PO |
|---|---|---|
| `status` | Trạng thái container, health check URL production | Từng phần đang chạy hay không, bằng lời thường |
| `logs` | Log 200 dòng gần nhất của backend (và service khác nếu cần) | Tóm tắt lỗi đáng chú ý. Không dán log thô dài |
| `backup` | Backup ngay | Tên file và thời điểm |
| `backups` | Liệt kê backup | Danh sách kèm ngày giờ, dung lượng |
| `rollback` | Xác nhận với PO, rồi quay lại bản trước | `pm deploy-log … --result rolled_back` |
| `restore` | **Nguy hiểm, ghi đè dữ liệu** (xem dưới) | Kết quả khôi phục |

Quy trình `restore`:
1. Liệt kê backup, PO chọn file.
2. Cảnh báo rõ: "Dữ liệu hiện tại sẽ bị thay bằng dữ liệu lúc …".
3. Xác nhận 2 lần.
4. Backup ngay trạng thái hiện tại.
5. Khôi phục.

Không bao giờ in nội dung `.deploy/.env.prod` hay mật khẩu ra màn hình.
