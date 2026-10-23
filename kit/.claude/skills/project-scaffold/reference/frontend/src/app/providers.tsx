"use client";

import type { ReactNode } from "react";
import { HttpHealthApi } from "@/services/api/health-api";
import { createHttpClient } from "@/services/api/http-client";
import { HttpUserApi } from "@/services/api/user-api";
import { ApiProvider, type Apis } from "@/services/api-context";

// Composition root của frontend: nơi DUY NHẤT tạo implementation HTTP thật.
const http = createHttpClient();
const apis: Apis = { userApi: new HttpUserApi(http), healthApi: new HttpHealthApi(http) };

export function Providers({ children }: { children: ReactNode }) {
  return <ApiProvider apis={apis}>{children}</ApiProvider>;
}
