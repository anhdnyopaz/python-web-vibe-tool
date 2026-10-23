"use client";

import { useEffect, useState } from "react";
import type { Health, ServiceState } from "@/services/api/interfaces";
import { useApi } from "@/services/api-context";

type Row = { key: string; label: string; detail: string; state: ServiceState | "checking" };

const LABELS: Record<ServiceState | "checking", string> = { ok: "Hoạt động", down: "Không phản hồi", checking: "Đang kiểm tra" };

function rowsFrom(health: Health | null, failed: boolean): Row[] {
  const pick = (value: ServiceState | undefined): Row["state"] => (failed ? "down" : value ?? "checking");
  return [
    { key: "web", label: "Giao diện", detail: "Next.js", state: "ok" },
    { key: "api", label: "Máy chủ API", detail: "FastAPI", state: failed ? "down" : health ? "ok" : "checking" },
    { key: "database", label: "Cơ sở dữ liệu", detail: "PostgreSQL", state: pick(health?.database) },
    { key: "cache", label: "Bộ nhớ đệm", detail: "Redis", state: pick(health?.cache) },
  ];
}

export function SystemStatus() {
  const { healthApi } = useApi();
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    healthApi
      .check()
      .then((result) => active && setHealth(result))
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, [healthApi]);

  return (
    <ul className="mt-10 max-w-xl divide-y divide-line border-y border-line" aria-label="Tình trạng hệ thống">
      {rowsFrom(health, failed).map((row, index) => (
        <li key={row.key} data-testid={`status-${row.key}`} data-state={row.state} className="flex items-center gap-4 py-4">
          <span
            aria-hidden
            style={{ transitionDelay: `${index * 120}ms` }}
            className={`size-3 rounded-full transition-colors duration-500 ${
              row.state === "ok" ? "bg-ok" : row.state === "down" ? "bg-down" : "animate-pulse bg-line"
            }`}
          />
          <span className="flex-1">
            <span className="font-semibold">{row.label}</span>
            <span className="ml-2 text-sm text-muted">{row.detail}</span>
          </span>
          <span className={`text-sm font-semibold ${row.state === "down" ? "text-down" : row.state === "ok" ? "text-ok" : "text-muted"}`}>
            {LABELS[row.state]}
          </span>
        </li>
      ))}
    </ul>
  );
}
