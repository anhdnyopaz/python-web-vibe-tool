"use client";

import { useCallback, useEffect, useState } from "react";
import type { User } from "@/services/api/interfaces";
import { useApi } from "@/services/api-context";
import { RegisterUserForm } from "./RegisterUserForm";
import { UserList } from "./UserList";

export function UsersPanel() {
  const { userApi } = useApi();
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    userApi
      .list()
      .then((items) => {
        setUsers(items);
        setError(null);
      })
      .catch((cause: Error) => setError(cause.message));
  }, [userApi]);

  useEffect(refresh, [refresh]);

  return (
    <div className="mt-8 grid items-start gap-8 md:grid-cols-[minmax(0,22rem)_1fr]">
      <div className="md:sticky md:top-6">
        <RegisterUserForm onRegistered={refresh} />
      </div>
      <div>
        {error && (
          <p role="alert" className="mb-4 font-semibold text-down">
            {error}
          </p>
        )}
        {users === null && !error ? <p className="text-muted">Đang tải danh sách…</p> : <UserList users={users ?? []} />}
      </div>
    </div>
  );
}
