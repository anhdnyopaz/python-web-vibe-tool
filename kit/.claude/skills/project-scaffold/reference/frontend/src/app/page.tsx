import Link from "next/link";
import { SystemStatus } from "@/features/system/components/SystemStatus";

export default function HomePage() {
  return (
    <section className="pt-10 sm:pt-16">
      <h1 className="max-w-2xl text-4xl leading-[1.1] font-extrabold tracking-tight sm:text-6xl">
        Ứng dụng của bạn đang chạy.
      </h1>
      <p className="mt-5 max-w-xl text-lg text-muted">
        Mỗi lần mở trang này, hệ thống tự kiểm tra các bộ phận bên dưới. Tất cả đều xanh nghĩa là sẵn sàng để làm tính năng mới.
      </p>
      <SystemStatus />
      <Link
        href="/users"
        className="mt-10 inline-flex rounded-lg bg-brand px-5 py-3 font-semibold text-brand-ink hover:opacity-90"
      >
        Xem danh sách thành viên
      </Link>
    </section>
  );
}
