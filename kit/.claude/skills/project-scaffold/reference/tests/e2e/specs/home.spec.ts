import { expect, test } from "@playwright/test";

test("trang chủ cho thấy mọi thành phần hệ thống đang hoạt động", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Ứng dụng của bạn đang chạy.");
  for (const part of ["web", "api", "database", "cache"]) {
    await expect(page.getByTestId(`status-${part}`)).toHaveAttribute("data-state", "ok");
  }
});
