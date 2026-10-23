---
name: testing-rules
description: Tiêu chuẩn kiểm thử bắt buộc — unit test (pytest, bun test), integration test, Hurl cho API, Playwright cho UI; cách ánh xạ tiêu chí chấp nhận sang test, ngưỡng coverage, cách xử lý test đỏ/flaky. Dùng khi viết hoặc sửa test, khi verify.
user-invocable: false
---

# Kim tự tháp test

| Tầng | Công cụ | Khi nào bắt buộc | Chạy bằng |
|---|---|---|---|
| Unit | pytest (backend), bun test (frontend) | **Mọi** thay đổi logic | `make test-unit` |
| Integration | pytest + Postgres thật | Repository mới hoặc thay đổi | `make test-integration` (nằm trong `test-api`) |
| API | Hurl | Task có `--api` (endpoint mới hoặc đổi) | `make test-api` |
| UI E2E | Playwright | Task có `--ui` (luồng người dùng mới hoặc đổi) | `make test-e2e` |

`pm verify` tự chọn gate theo cờ của task: lint + unit luôn chạy, cộng api/e2e nếu task có cờ.

# Từ AC đến test

- Mỗi AC Given/When/Then phải có **ít nhất một** test chứng minh, ở tầng thấp nhất có thể chứng minh được:
  - quy tắc nghiệp vụ → unit test service
  - định dạng response → Hurl
  - người dùng thấy hoặc bấm được → Playwright
- Ghi bằng `pm ac T-xxx N --evidence "<đường dẫn test>::<tên test>"`.
- Tên test mô tả hành vi: `test_register_rejects_duplicate_email`, `it("shows the server error message")`.

# Unit test

- Mẫu Arrange / Act / Assert, mỗi test kiểm tra một hành vi. Không phụ thuộc thứ tự chạy, mạng, đồng hồ thật (inject `IClock` nếu cần).
- Phụ thuộc được thay bằng **fake implement interface** (`tests/fakes/`, `frontend/test/fakes.ts`). Hạn chế mock; không bao giờ mock chính class đang test.
- Phải có cả trường hợp lỗi và biên: rỗng, quá dài, trùng, không tồn tại, sai định dạng, phân trang.
- Ngưỡng coverage: backend 80% (`pyproject.toml`), frontend 70% (`bunfig.toml`). Không được hạ.

# Hurl (`tests/api/<resource>.hurl`)

- Một file cho mỗi resource. Mỗi request có comment tiếng Việt nói mục đích.
- Dùng `{{base_url}}`. Dữ liệu duy nhất bằng `{{newUuid}}`, để test chạy lại nhiều lần và chạy song song không đụng nhau.
- Kiểm tra mã HTTP **và** nội dung (`jsonpath`). Phải có các ca lỗi 404/409/422 và `$.error.code`.
- Dùng `[Captures]` để nối chuỗi request (tạo → đọc → sửa → xoá).

# Playwright (`tests/e2e/specs/<flow>.spec.ts`)

- Mỗi spec là một luồng người dùng, tên test bằng tiếng Việt mô tả điều người dùng làm được.
- Locator ưu tiên theo thứ tự: `getByRole`, rồi `getByLabel`, rồi `getByTestId`. Không dùng CSS selector dễ vỡ, không dùng `waitForTimeout`; dùng `expect(...).toHaveX` (tự chờ).
- Next.js luôn có sẵn một `role="alert"` ẩn (route announcer). Vì vậy `getByRole("alert")` phải được **giới hạn trong vùng** chứa nó, ví dụ `page.getByRole("form", { name: "…" }).getByRole("alert")`.
- Dữ liệu duy nhất cho mỗi lần chạy (`Date.now()` + chuỗi ngẫu nhiên). Không phụ thuộc dữ liệu có sẵn.
- Chạy trên cả `desktop` và `mobile`. Giao diện vỡ trên mobile là lỗi.
- Khi fail: đọc `tests/e2e/test-results/` (trace, screenshot) để tìm nguyên nhân.

# Test đỏ, flaky

- Test đỏ: tìm nguyên nhân gốc. Chỉ sửa test khi chính test sai, và ghi lý do bằng `pm note`.
- Test chập chờn (flaky) là lỗi thật: sửa cách chờ hoặc dữ liệu, không thêm retry hay sleep để che.
- **Tuyệt đối không:** `@pytest.mark.skip`, `it.skip`, `test.only`, xoá assertion, hạ ngưỡng, `--no-verify`.
