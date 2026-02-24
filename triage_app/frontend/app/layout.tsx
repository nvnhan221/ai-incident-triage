import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Incident Triage",
  description: "Tìm log và gợi ý xử lý incident từ mã đơn / merchant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="bg-[var(--bg)] text-[var(--text)]">{children}</body>
    </html>
  );
}
