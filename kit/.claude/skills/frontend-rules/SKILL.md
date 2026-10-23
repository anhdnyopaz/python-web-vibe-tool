---
name: frontend-rules
description: Quy ước frontend Next.js 16 + Tailwind CSS 4 + TypeScript + Bun — cấu trúc thư mục, interface service, ApiProvider, design system trong docs/DESIGN.md, test bằng bun test, data-testid cho Playwright. Dùng mỗi khi sửa code trong frontend/.
user-invocable: false
---

# Bắt buộc: skill frontend-design

Mọi giao diện mới hoặc thay đổi giao diện phải theo skill **frontend-design** (đã nạp sẵn cho techlead).

1. Đọc `docs/DESIGN.md` trước.
2. **Chưa có `docs/DESIGN.md`** (lần đầu làm UI của dự án): lập design plan theo đúng quy trình của skill. Dựa trên chủ đề sản phẩm trong `docs/PRD.md`, gồm:
   - màu (4–6 mã hex có tên)
   - typography
   - bố cục (có wireframe ASCII)
   - nguyên tắc

   Tự review plan theo checklist "default/cliché" của skill. Ghi plan vào `docs/DESIGN.md`. Chuyển token vào `@theme` trong `frontend/src/app/globals.css`.
3. **Đã có:** tuân theo nó. Muốn đổi design system thì hỏi PO (`pm ask`), không tự đổi.
4. Chữ trên giao diện viết **tiếng Việt** theo phần "writing" của skill: nút ghi rõ hành động, lỗi chỉ cách sửa, trạng thái rỗng mời hành động.
5. Chất lượng tối thiểu:
   - responsive tới 360px
   - focus nhìn thấy được khi dùng bàn phím
   - tương phản AA
   - tôn trọng `prefers-reduced-motion`
   - có đủ trạng thái loading / rỗng / lỗi

Hook `require_design.py` sẽ **từ chối** sửa file `.tsx/.css` trong `frontend/src` nếu skill chưa được nạp trong phiên.

# Cấu trúc

```
frontend/src/
├── app/                      # route, page MỎNG: chỉ ghép component, không gọi fetch
│   ├── layout.tsx, globals.css (design tokens @theme), providers.tsx (composition root)
│   └── <route>/page.tsx
├── features/<feature>/components/   # component + test cạnh nhau (X.tsx + X.test.tsx)
├── services/
│   ├── api/interfaces.ts     # PORT: type dữ liệu + I<Name>Api
│   ├── api/http-client.ts    # fetch chung, ApiError
│   ├── api/<name>-api.ts     # ADAPTER: Http<Name>Api implements I<Name>Api (+ test)
│   └── api-context.tsx       # ApiProvider + useApi()
frontend/test/                # happydom.ts, testing-library.ts (preload), fakes.ts (Fake<Name>Api)
```

Luật (kiểm bằng `src/architecture.test.ts`):
- Component trong `features/` chỉ lấy dữ liệu qua `useApi()` và **interface**. Không import `http-client` hoặc `*-api.ts`, không gọi `fetch(`.
- Chỉ `app/providers.tsx` được tạo `new Http<Name>Api(...)`.
- API mới cần làm đủ 4 việc:
  1. thêm interface vào `interfaces.ts`
  2. viết `Http<Name>Api` kèm test
  3. thêm `Fake<Name>Api` vào `test/fakes.ts`
  4. thêm vào type `Apis` và `providers.tsx`
- Gọi API bằng đường dẫn tương đối `/api/...` (cùng domain qua Traefik). Không dùng `NEXT_PUBLIC_API_URL`, không cấu hình CORS.
- DTO backend dùng `snake_case`; chuyển sang `camelCase` trong adapter `*-api.ts`.

# Component & state

- Mặc định là Server Component. Thêm `"use client"` khi cần state, effect hoặc `useApi()`.
- Form: `<label>` bọc input, có `required`/`type` hợp lệ, hiển thị lỗi bằng `role="alert"`, khoá nút khi đang gửi.
- Phần tử Playwright cần dùng có `data-testid` (kebab-case). Ưu tiên `getByRole` trong test khi có thể.
- Không thêm UI kit hoặc thư viện state khi chưa có ADR. Tailwind + React là đủ cho hầu hết trường hợp.

# Test (bun test, coverage ≥ 70%)

- Đặt cạnh file nguồn: `X.test.tsx`. Import `describe/it/expect/mock` từ `bun:test`, `render/screen/waitFor` từ `@testing-library/react`, `userEvent` từ `@testing-library/user-event`.
- Bọc component bằng `<ApiProvider apis={{ userApi: new FakeUserApi(), ... }}>`.
- Test hành vi người dùng (gõ, bấm, thấy chữ), không test chi tiết cài đặt.
- Phải test cả các trạng thái: thành công, lỗi từ server, rỗng, đang tải (nếu có logic).
- Chạy: `make test-unit-fe`. Typecheck: `make lint-fe`.

# Lệnh

- Thêm thư viện: `docker compose run --rm --no-deps frontend bun add <pkg>@<version>` (`-d` cho dev).
- Next dev chạy trong container `frontend` (hot reload qua volume). Đổi `package.json` thì có thể cần `make deps` hoặc `docker compose restart frontend`.
