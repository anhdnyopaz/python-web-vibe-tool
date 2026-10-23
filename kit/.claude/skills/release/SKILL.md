---
name: release
description: Chốt một phiên bản phát hành — chạy toàn bộ kiểm thử, cập nhật CHANGELOG, gắn tag phiên bản (và push nếu có remote). Dùng trước khi deploy hoặc khi người dùng gõ /release.
argument-hint: "[phiên bản, ví dụ v0.2.0]"
---

# /release — Chốt phiên bản

Phiên bản PO đề nghị: $ARGUMENTS (để trống thì TechLead đề xuất theo SemVer).

1. `git remote -v`: nếu có remote, hỏi PO có muốn đẩy code và tag lên GitHub/GitLab không. Đây là hành động ra bên ngoài.
2. Giao Agent `subagent_type: "techlead"`:
   > Chế độ RELEASE. Phiên bản: <vX.Y.Z hoặc tự đề xuất>. Push: <có/không>. Trả báo cáo theo mẫu, kèm danh sách thay đổi bằng lời thường.
3. Báo PO:
   - Tên phiên bản.
   - Những gì mới trong bản này (lấy từ CHANGELOG, viết lại dễ hiểu).
   - Gợi ý `/deploy` để đưa bản này lên Internet.
