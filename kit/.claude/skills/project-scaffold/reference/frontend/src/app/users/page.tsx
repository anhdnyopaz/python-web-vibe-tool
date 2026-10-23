import { UsersPanel } from "@/features/users/components/UsersPanel";

export default function UsersPage() {
  return (
    <section className="pt-8">
      <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Thành viên</h1>
      <p className="mt-2 max-w-xl text-muted">Thêm người mới và xem ai đã tham gia gần đây.</p>
      <UsersPanel />
    </section>
  );
}
