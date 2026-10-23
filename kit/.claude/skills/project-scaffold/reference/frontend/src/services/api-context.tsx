"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { IHealthApi, IUserApi } from "./api/interfaces";

export type Apis = { userApi: IUserApi; healthApi: IHealthApi };

const ApiContext = createContext<Apis | null>(null);

export function ApiProvider({ apis, children }: { apis: Apis; children: ReactNode }) {
  return <ApiContext.Provider value={apis}>{children}</ApiContext.Provider>;
}

export function useApi(): Apis {
  const apis = useContext(ApiContext);
  if (!apis) throw new Error("useApi() phải nằm trong <ApiProvider>");
  return apis;
}
