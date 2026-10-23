import { describe, expect, it } from "bun:test";
import type { HttpClient } from "./http-client";
import { HttpUserApi } from "./user-api";

describe("HttpUserApi", () => {
  it("maps snake_case DTOs to User", async () => {
    const http = (async () => ({ items: [{ id: 1, email: "an@example.com", full_name: "An", created_at: null }] })) as HttpClient;
    expect(await new HttpUserApi(http).list()).toEqual([{ id: 1, email: "an@example.com", fullName: "An", createdAt: null }]);
  });

  it("sends snake_case body when registering", async () => {
    let sent: RequestInit | undefined;
    const http = (async (_path: string, init?: RequestInit) => {
      sent = init;
      return { id: 2, email: "binh@example.com", full_name: "Bình", created_at: null };
    }) as HttpClient;
    const user = await new HttpUserApi(http).register({ email: "binh@example.com", fullName: "Bình" });
    expect(JSON.parse(String(sent?.body))).toEqual({ email: "binh@example.com", full_name: "Bình" });
    expect(user.fullName).toBe("Bình");
  });
});
