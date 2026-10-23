---
name: progress
description: Báo cáo tiến độ dự án bằng ngôn ngữ dễ hiểu — đã xong gì, đang làm gì, việc gì đang chờ PO. Dùng khi người dùng hỏi tiến độ, tình hình dự án hoặc gõ /progress.
---

# /progress — Tiến độ dự án

1. Chạy `python3 .claude/tools/pm.py status` và `python3 .claude/tools/pm.py list --all`.
2. Tóm tắt cho PO trong ≤ 12 dòng, không dùng mã nội bộ trừ khi cần:
   - **Tiến độ:** % hoàn thành, từng milestone.
   - **Vừa xong:** 3 việc gần nhất.
   - **Đang làm.**
   - **Tiếp theo:** 2–3 việc.
   - **Cần PO:** câu hỏi đang chờ, việc chờ nghiệm thu, việc bị chặn và lý do. Nếu có thì hỏi luôn bằng AskUserQuestion.
   - **Bản online** (nếu có): link chia sẻ, link production, lần deploy gần nhất.
3. Gợi ý `/board` nếu PO muốn xem bảng trực quan.
