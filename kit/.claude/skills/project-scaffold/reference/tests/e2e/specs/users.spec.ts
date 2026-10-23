import { expect, test } from "@playwright/test";

test("thêm thành viên mới và thấy ngay trong danh sách", async ({ page }) => {
  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
  await page.goto("/users");

  await page.getByTestId("full-name").fill("Người Thử E2E");
  await page.getByTestId("email").fill(email);
  await page.getByTestId("register-submit").click();

  await expect(page.getByTestId("user-list")).toContainText(email);
  await expect(page.getByTestId("email")).toHaveValue("");
});

test("báo lỗi rõ ràng khi email đã được đăng ký", async ({ page }) => {
  const email = `dup-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
  await page.goto("/users");
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.getByTestId("full-name").fill("Trùng Email");
    await page.getByTestId("email").fill(email);
    await page.getByTestId("register-submit").click();
    if (attempt === 0) await expect(page.getByTestId("user-list")).toContainText(email);
  }
  // Giới hạn trong form: Next.js luôn có sẵn một phần tử role="alert" ẩn (route announcer).
  await expect(page.getByRole("form", { name: "Thêm thành viên" }).getByRole("alert")).toContainText("đã được đăng ký");
});
