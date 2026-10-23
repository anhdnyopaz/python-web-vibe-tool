import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import Link from "next/link";
import type { ReactNode } from "react";
import { Providers } from "./providers";
import "./globals.css";

const beVietnam = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-be-vietnam",
});

export const metadata: Metadata = {
  title: "Ứng dụng mới",
  description: "Khung dự án FastAPI + Next.js",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className={beVietnam.variable}>
      <body className="min-h-dvh font-sans">
        <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-5 sm:px-6">
          <Link href="/" className="text-lg font-extrabold tracking-tight">
            Ứng dụng mới
          </Link>
          <nav className="flex gap-5 text-sm font-semibold text-muted">
            <Link href="/" className="hover:text-ink">Tổng quan</Link>
            <Link href="/users" className="hover:text-ink">Thành viên</Link>
          </nav>
        </header>
        <Providers>
          <main className="mx-auto max-w-5xl px-4 pb-20 sm:px-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
