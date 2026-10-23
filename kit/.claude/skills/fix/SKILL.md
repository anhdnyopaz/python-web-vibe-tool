---
name: fix
description: Báo lỗi — thu thập mô tả lỗi từ PO, ghi nhận và giao TechLead tái hiện bằng test rồi sửa tận gốc. Dùng khi người dùng báo app bị lỗi, chạy sai, hoặc gõ /fix.
argument-hint: "<mô tả lỗi: làm gì, mong đợi gì, thấy gì>"
---

# /fix — Báo lỗi

Mô tả của PO: $ARGUMENTS

1. Mô tả cần đủ 3 ý: **đã làm gì** (trang nào, bấm gì), **mong đợi gì**, **thực tế thấy gì** (thông báo lỗi, ảnh chụp nếu có). Thiếu ý nào thì hỏi 1 lượt bằng AskUserQuestion.
2. Ghi nhận:
   ```bash
   python3 .claude/tools/pm.py request bug "<mô tả đầy đủ>" [--task T-xxx nếu biết lỗi ở việc nào]
   ```
3. Giao Agent `subagent_type: "techlead"`:
   > Chế độ BUGFIX cho yêu cầu R-xxx: <mô tả>.
   > - Tạo task bug (`--from R-xxx`).
   > - Tái hiện bằng test đỏ trước, rồi sửa nguyên nhân gốc.
   > - Verify, commit, merge như BUILD.
   >
   > Trả báo cáo theo mẫu, có nguyên nhân gốc bằng lời thường.
4. Báo PO:
   - Nguyên nhân (1–2 câu dễ hiểu).
   - Đã sửa gì.
   - Cách thử lại.
   - Đã thêm bài kiểm tra tự động để lỗi không quay lại.
