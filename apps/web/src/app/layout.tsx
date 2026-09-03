import type { Metadata } from "next";
import { Geist } from "next/font/google";

import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-geist-ui",
});

export const metadata: Metadata = {
  title: "Portal · 内部业务系统",
  description: "合同与发票两个独立模块的公司内部工作台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={`${geist.variable} antialiased`}>{children}</body>
    </html>
  );
}
