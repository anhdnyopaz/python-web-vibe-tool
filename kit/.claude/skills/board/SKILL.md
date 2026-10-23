---
name: board
description: Mở bảng điều hành dự án (dashboard web ở http://localhost:4000) để PO xem tiến độ, trả lời câu hỏi, gửi yêu cầu, nghiệm thu. Dùng khi người dùng muốn xem bảng, dashboard hoặc gõ /board.
---

# /board — Bảng điều hành dự án

1. Kiểm tra dashboard đã chạy chưa: `curl -s -o /dev/null -w '%{http_code}' http://localhost:4000/api/state`.
2. Chưa chạy (khác 200): chạy nền bằng Bash với `run_in_background: true`:
   ```bash
   python3 .claude/tools/pm.py serve --open
   ```
   Nếu cổng 4000 bận thì dùng `--port 4001`.
3. Nói với PO:
   - Bảng ở http://localhost:4000 (đã tự mở trình duyệt), tự cập nhật mỗi 5 giây.
   - Dải màu vàng là việc cần bạn: trả lời câu hỏi, thử và nghiệm thu.
   - Ô "Gửi yêu cầu" để ghi ý tưởng hoặc lỗi bất cứ lúc nào. TechLead sẽ xử lý ở lần `/next` tiếp theo.
   - Nút "Sao chép" để lấy lệnh dán vào Claude Code.
