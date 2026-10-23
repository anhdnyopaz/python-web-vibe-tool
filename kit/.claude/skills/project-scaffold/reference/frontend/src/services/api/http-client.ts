export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type HttpClient = <T>(path: string, init?: RequestInit) => Promise<T>;

type ErrorBody = { error?: { code?: string; message?: string }; detail?: unknown };

// Gọi API cùng domain qua Traefik (/api/...), nên không cần cấu hình CORS.
export function createHttpClient(baseUrl = "", fetcher: typeof fetch = fetch): HttpClient {
  return async function request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await fetcher(`${baseUrl}${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init?.headers },
      });
    } catch {
      throw new ApiError("Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.", 0, "network_error");
    }
    const body = (await response.json().catch(() => ({}))) as ErrorBody & T;
    if (!response.ok) {
      const message = body.error?.message ?? (response.status === 422 ? "Dữ liệu chưa hợp lệ" : "Máy chủ đang gặp lỗi, thử lại sau");
      throw new ApiError(message, response.status, body.error?.code ?? "http_error");
    }
    return body;
  };
}
