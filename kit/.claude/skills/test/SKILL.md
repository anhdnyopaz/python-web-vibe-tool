---
name: test
description: Chạy toàn bộ kiểm thử tự động (lint, unit, API, giao diện) và giải thích kết quả bằng lời thường. Dùng khi người dùng muốn kiểm tra chất lượng hoặc gõ /test.
---

# /test — Kiểm tra toàn bộ

1. Chạy `python3 .claude/tools/pm.py verify --all` (Bash timeout 600000).
2. Báo PO theo từng nhóm, bằng lời thường:

   | Nhóm | Gọi là |
   |---|---|
   | lint | Kiểm tra quy chuẩn code và kiến trúc |
   | unit | Kiểm tra từng phần nhỏ |
   | api | Kiểm tra máy chủ API |
   | e2e | Kiểm tra giao diện như người dùng thật, trên máy tính và điện thoại |

   Đạt hay không đạt, và số lượng nếu log có.
3. Có nhóm không đạt:
   - Đọc `.pm/logs/<gate>.log`, tóm tắt nguyên nhân.
   - Hỏi PO có muốn giao TechLead sửa ngay không. Đồng ý thì giao `techlead` chế độ BUGFIX.
