"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LogoLockup } from "@/components/logo";
import { api } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";

const NAV = [
  { href: "/", label: "总览", hint: "工作台" },
  { href: "/contracts", label: "合同", hint: "独立模块" },
  { href: "/invoices", label: "发票", hint: "独立模块" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    api<CurrentUser>("/api/v1/auth/me")
      .then(setUser)
      .catch(() => undefined);
  }, []);

  async function logout() {
    await api("/api/v1/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="bg-surface-alt px-5 py-6 lg:min-h-screen">
        <LogoLockup />
        <nav className="mt-8 space-y-1">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-[18px] px-3 py-2 ${
                  active ? "bg-paper font-medium text-ink" : "text-ink hover:bg-paper"
                }`}
              >
                <span className="block text-[14px]">{item.label}</span>
                <span className="block text-[12px] tracking-[0.6px] text-mid-gray uppercase">{item.hint}</span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-10 pt-5 text-body">
          <p className="font-medium text-ink">{user?.name ?? "加载中…"}</p>
          <p className="mt-1 text-mid-gray">{user?.role === "admin" ? "管理员" : "成员"}</p>
          <button type="button" onClick={logout} className="mt-3 font-medium text-ink underline-offset-4 hover:underline">
            退出登录
          </button>
        </div>
      </aside>
      <div>
        <main className="mx-auto w-full max-w-[1280px] px-5 py-8 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
