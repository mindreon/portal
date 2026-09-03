import type { Metadata } from "next";
import { Hedvig_Letters_Serif, Inter } from "next/font/google";

import "./globals.css";

const hedvig = Hedvig_Letters_Serif({
  subsets: ["latin"],
  variable: "--font-hedvig",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-inter-ui",
});

export const metadata: Metadata = {
  title: "Portal · 内部业务系统",
  description: "合同与发票两个独立模块的公司内部工作台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={`${hedvig.variable} ${inter.variable} antialiased`}>{children}</body>
    </html>
  );
}
