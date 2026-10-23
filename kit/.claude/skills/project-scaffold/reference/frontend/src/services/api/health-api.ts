import { ApiError, type HttpClient } from "./http-client";
import type { Health, IHealthApi } from "./interfaces";

export class HttpHealthApi implements IHealthApi {
  constructor(private readonly http: HttpClient) {}

  async check(): Promise<Health> {
    try {
      return await this.http<Health>("/api/health");
    } catch (error) {
      // API trả 503 khi DB/Redis lỗi — vẫn muốn hiển thị từng thành phần nên coi là "down".
      if (error instanceof ApiError && error.status === 503) {
        return { status: "down", database: "down", cache: "down" };
      }
      throw error;
    }
  }
}
