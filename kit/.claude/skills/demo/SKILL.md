---
name: demo
description: Bật ứng dụng trên máy và đưa link để PO mở thử. Dùng khi người dùng muốn xem/chạy/mở ứng dụng hoặc gõ /demo.
---

# /demo — Mở ứng dụng

1. `docker info` (im lặng). Lỗi thì hướng dẫn PO mở Docker Desktop và chờ biểu tượng cá voi đứng yên.
2. Chạy `make up` (Bash timeout 600000). Lần đầu build mất vài phút. Báo PO đang khởi động.
3. Thành công: đưa link
   - Ứng dụng: http://localhost:8080
   - Tài liệu API (cho người kỹ thuật): http://localhost:8080/api/docs
4. Thất bại: đọc `make ps` và `docker compose logs --tail=80`. Cổng 8080 bị chiếm thì đặt `APP_PORT=8081` trong `.env` rồi thử lại. Lỗi do code thì giao `techlead` chế độ BUGFIX.
5. Gợi ý `/preview` nếu PO muốn gửi link cho người khác xem.
