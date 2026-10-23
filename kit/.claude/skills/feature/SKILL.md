---
name: feature
description: Thêm yêu cầu/tính năng mới vào dự án — làm rõ với PO, ghi nhận, giao TechLead phân tích thành task có tiêu chí chấp nhận. Dùng khi người dùng muốn thêm, đổi một tính năng hoặc gõ /feature.
argument-hint: "<mô tả tính năng bằng lời thường>"
---

# /feature — Thêm yêu cầu mới

Yêu cầu của PO: $ARGUMENTS

1. **Thiếu mô tả hoặc quá mơ hồ** (ví dụ "thêm báo cáo"): hỏi tối đa 1 lượt bằng AskUserQuestion. Hỏi ai dùng, để làm gì, ví dụ cụ thể. Mô tả đã đủ thì bỏ qua.
2. Ghi nhận:
   ```bash
   python3 .claude/tools/pm.py request feature "<mô tả đã làm rõ>"
   ```
3. Giao Agent `subagent_type: "techlead"`:
   > Chế độ PLAN. Phân tích các yêu cầu mới trong `pm inbox` (gồm R-xxx vừa tạo).
   > - Cập nhật PRD nếu phạm vi đổi.
   > - Tạo task (`--from R-xxx`) có AC, cờ `--api`/`--ui`, ưu tiên hợp lý.
   > - Câu hỏi nghiệp vụ thì ghi bằng `pm ask`.
   > - KHÔNG code.
   >
   > Trả báo cáo theo mẫu.
4. Trình bày cho PO bằng lời thường:
   - Yêu cầu được chia thành những việc gì.
   - Thứ tự làm.
   - Ước lượng tương đối: nhỏ / vừa / lớn.
5. Có câu hỏi đang chờ thì hỏi luôn bằng AskUserQuestion, lưu bằng `pm answer`.
6. Gợi ý bước tiếp: `/next`.
