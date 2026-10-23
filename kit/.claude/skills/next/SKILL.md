---
name: next
description: Làm việc tiếp theo trong kế hoạch — giao TechLead xử lý yêu cầu mới, làm task ưu tiên nhất theo đúng quy trình (test trước, verify, commit), rồi báo kết quả và cách thử cho PO. Dùng khi người dùng muốn tiếp tục làm, "làm tiếp", hoặc gõ /next.
argument-hint: "[số việc muốn làm liên tiếp, mặc định 1]"
---

# /next — Làm việc tiếp theo

Số việc muốn làm liên tiếp: $ARGUMENTS (để trống nghĩa là 1, tối đa 5).

Lặp lại các bước sau cho từng việc:

1. Chạy `python3 .claude/tools/pm.py status`.
   - **Có câu hỏi đang chờ PO:** hỏi bằng AskUserQuestion, lưu bằng `pm answer`.
   - **Có task "Chờ nghiệm thu":** nhắc PO thử trước (xem bước 4).
2. **Có yêu cầu mới trong inbox** (`pm inbox` không trống, ví dụ PO gửi từ dashboard): giao `techlead` chế độ PLAN cho các yêu cầu đó trước, giống `/feature` bước 3.
3. Giao Agent `subagent_type: "techlead"`:
   > Chế độ BUILD. Làm task tiếp theo theo `pm next` (hoặc tiếp tục task đang làm dở). Tuân thủ đầy đủ quy trình BUILD và checklist tự review. Trả báo cáo theo mẫu.

   Timeout dài: gate test chạy trong Docker.
4. Chuyển báo cáo cho PO **bằng lời thường**:
   - **Đã làm được gì:** người dùng giờ làm được việc gì.
   - **Cách thử:** link và các bước bấm.
   - **Chất lượng:** "đã qua N bài kiểm tra tự động", không liệt kê tên tool.
   - **Câu hỏi cần PO trả lời** (nếu có).

   Đừng dán nguyên báo cáo kỹ thuật. Chỉ đưa phần "Chi tiết kỹ thuật" nếu PO hỏi.
5. Task ở trạng thái **Chờ nghiệm thu** (cấu hình `require_acceptance`): hỏi bằng AskUserQuestion: "Chấp nhận" / "Chưa ổn (ghi lý do)".
   - Chấp nhận: `pm accept T-xxx`.
   - Chưa ổn: `pm reject T-xxx "<lý do>"`, rồi giao techlead sửa ngay (BUILD tiếp tục task đó).
6. Kết quả "Bị chặn" hoặc "Thất bại": giải thích nguyên nhân bằng lời thường và việc PO cần làm. **Dừng vòng lặp.**

Cuối cùng gợi ý: `/next` để làm tiếp, `/board` để xem tổng quan, `/preview` để gửi link cho người khác xem.
