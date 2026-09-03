import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Portal 内部业务系统",
  description: "合同、发票与后续业务模块的公司内部管理系统",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
