import { describe, expect, it } from "bun:test";
import { HttpHealthApi } from "./health-api";
import { ApiError, type HttpClient } from "./http-client";

describe("HttpHealthApi", () => {
  it("returns health payload", async () => {
    const http = (async () => ({ status: "ok", database: "ok", cache: "ok" })) as HttpClient;
    expect((await new HttpHealthApi(http).check()).status).toBe("ok");
  });

  it("treats 503 as down", async () => {
    const http = (async () => {
      throw new ApiError("down", 503, "http_error");
    }) as HttpClient;
    expect((await new HttpHealthApi(http).check()).database).toBe("down");
  });

  it("rethrows other errors", async () => {
    const http = (async () => {
      throw new ApiError("offline", 0, "network_error");
    }) as HttpClient;
    await expect(new HttpHealthApi(http).check()).rejects.toThrow("offline");
  });
});
