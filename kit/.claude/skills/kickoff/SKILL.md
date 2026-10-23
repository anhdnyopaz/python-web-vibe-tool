---
name: kickoff
description: Bắt đầu dự án mới — phỏng vấn Product Owner bằng ngôn ngữ thường, viết PRD, giao TechLead dựng khung dự án và lập kế hoạch task. Dùng khi người dùng muốn bắt đầu/khởi tạo dự án hoặc gõ /kickoff.
argument-hint: "[mô tả ngắn ý tưởng]"
---

# /kickoff — Khởi động dự án

Bạn (luồng chính) là **người điều phối**: nói chuyện với PO bằng tiếng Việt đơn giản, không thuật ngữ. Mọi việc kỹ thuật giao cho sub agent `techlead`.

Ý tưởng ban đầu từ người dùng: $ARGUMENTS

## Bước 1: Kiểm tra hiện trạng
- Chạy `python3 .claude/tools/pm.py status`.
- Nếu dự án đã khởi tạo và đã có `backend/`: nói với PO dự án đã có khung, đề nghị dùng `/feature` để thêm yêu cầu. Dừng.
- Chạy `docker info` (im lặng). Nếu lỗi, hướng dẫn PO cài hoặc mở **Docker Desktop** (https://www.docker.com/products/docker-desktop/) rồi chạy lại `/kickoff`.

## Bước 2: Phỏng vấn (tối đa 3 lượt, dùng AskUserQuestion)

Mỗi lượt hỏi 2–4 câu, có lựa chọn gợi ý cụ thể theo ý tưởng của PO.

- **Lượt 1:** sản phẩm giải quyết vấn đề gì, cho ai, và thành công trông như thế nào.
- **Lượt 2:** 3–7 việc quan trọng nhất người dùng phải làm được trong bản đầu tiên. Có cần đăng nhập không. Dùng trên máy tính hay điện thoại.
- **Lượt 3:** cái gì KHÔNG làm, phong cách giao diện / thương hiệu (màu, logo, trang web tham khảo), có hạn chót hay không.

Không hỏi chuyện kỹ thuật (database, framework…). Stack đã cố định.

## Bước 3: Viết PRD
- Tạo `docs/PRD.md` từ `.claude/skills/kickoff/templates/PRD.md`, điền theo câu trả lời.
- Những gì chưa rõ thì ghi vào mục "Câu hỏi còn mở".
- Tóm tắt PRD cho PO trong ≤ 10 dòng và hỏi: "Đúng ý bạn chưa?". Sửa tới khi PO đồng ý.

## Bước 4: Giao TechLead

Gọi Agent với `subagent_type: "techlead"`, prompt:

> Chế độ SCAFFOLD rồi PLAN. Tên dự án: "<tên>". PRD đã duyệt ở docs/PRD.md.
> (1) Dựng khung dự án theo skill project-scaffold, gồm cả design system cho sản phẩm này (docs/DESIGN.md) theo skill frontend-design.
> (2) Chia phạm vi MVP trong PRD thành milestone M1 (và M2 nếu cần), các task có AC Given/When/Then, cờ --api/--ui, thứ tự --after.
> (3) Câu hỏi nghiệp vụ còn mở thì ghi bằng pm ask.
> Trả báo cáo theo mẫu.

Đặt timeout đủ dài. Việc dựng lần đầu build Docker mất vài phút.

## Bước 5: Trình bày cho PO
- Kết quả dựng dự án: mở http://localhost:8080 để thấy ứng dụng chạy.
- Kế hoạch: danh sách milestone và task bằng lời thường (không cần mã T-xxx trừ khi PO hỏi).
- Câu hỏi đang chờ PO: hỏi luôn bằng AskUserQuestion, rồi lưu bằng `pm answer Q-xxx "…"`.
- Gợi ý bước tiếp:
  - `/next` để bắt đầu làm việc đầu tiên.
  - `/board` để mở bảng điều hành trực quan.
