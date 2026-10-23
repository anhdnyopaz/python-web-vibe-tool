import type { User } from "@/services/api/interfaces";

export function UserList({ users }: { users: User[] }) {
  if (users.length === 0) {
    return (
      <p data-testid="user-list-empty" className="rounded-[var(--radius-card)] border border-dashed border-line p-6 text-muted">
        Chưa có ai. Thêm thành viên đầu tiên bằng biểu mẫu bên cạnh.
      </p>
    );
  }
  return (
    <ul data-testid="user-list" className="divide-y divide-line rounded-[var(--radius-card)] border border-line bg-paper">
      {users.map((user) => (
        <li key={user.id} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 px-5 py-4">
          <span className="font-semibold">{user.fullName}</span>
          <span className="text-sm text-muted">{user.email}</span>
        </li>
      ))}
    </ul>
  );
}
