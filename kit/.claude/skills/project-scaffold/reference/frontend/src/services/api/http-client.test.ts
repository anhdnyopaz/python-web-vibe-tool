import { describe, expect, it } from "bun:test";
import { ApiError, createHttpClient } from "./http-client";

const respond = (status: number, body: unknown) =>
  (async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;

describe("createHttpClient", () => {
  it("returns parsed JSON on success", async () => {
    const http = createHttpClient("", respond(200, { hello: "world" }));
    expect(await http<{ hello: string }>("/api/x")).toEqual({ hello: "world" });
  });

  it("throws ApiError with server message", async () => {
    const http = createHttpClient("", respond(409, { error: { code: "conflict", message: "Email đã tồn tại" } }));
    const error = (await http("/api/x").catch((e) => e)) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe("Email đã tồn tại");
    expect(error.code).toBe("conflict");
  });

  it("uses a friendly message for validation errors without body", async () => {
    const http = createHttpClient("", respond(422, { detail: [] }));
    await expect(http("/api/x")).rejects.toThrow("Dữ liệu chưa hợp lệ");
  });

  it("maps network failures", async () => {
    const failing = (async () => {
      throw new TypeError("fetch failed");
    }) as unknown as typeof fetch;
    const error = (await createHttpClient("", failing)("/api/x").catch((e) => e)) as ApiError;
    expect(error.code).toBe("network_error");
  });
});
