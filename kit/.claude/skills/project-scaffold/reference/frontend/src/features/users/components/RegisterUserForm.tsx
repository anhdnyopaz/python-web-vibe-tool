"use client";

import { useState, type FormEvent } from "react";
import type { User } from "@/services/api/interfaces";
import { useApi } from "@/services/api-context";

export function RegisterUserForm({ onRegistered }: { onRegistered: (user: User) => void }) {
  const { userApi } = useApi();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const user = await userApi.register({ email, fullName });
      setEmail("");
      setFullName("");
      onRegistered(user);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Chưa thêm được thành viên, thử lại sau");
    } finally {
      setSaving(false);
    }
  }

  const field = "mt-1 w-full rounded-lg border border-line bg-paper px-3 py-2.5";
  return (
    <form onSubmit={handleSubmit} className="grid gap-4 rounded-[var(--radius-card)] border border-line bg-paper p-5" aria-label="Thêm thành viên">
      <h2 className="text-lg font-bold">Thêm thành viên</h2>
      <label className="text-sm font-semibold">
        Họ tên
        <input data-testid="full-name" required value={fullName} onChange={(e) => setFullName(e.target.value)} className={field} autoComplete="name" />
      </label>
      <label className="text-sm font-semibold">
        Email
        <input data-testid="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={field} autoComplete="email" />
      </label>
      {error && (
        <p role="alert" className="text-sm font-semibold text-down">
          {error}
        </p>
      )}
      <button data-testid="register-submit" type="submit" disabled={saving} className="rounded-lg bg-brand px-4 py-2.5 font-semibold text-brand-ink disabled:opacity-60">
        {saving ? "Đang thêm…" : "Thêm thành viên"}
      </button>
    </form>
  );
}
