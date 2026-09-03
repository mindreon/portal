"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LogoLockup } from "@/components/logo";
import { api } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";

const NAV = [
  { href: "/", label: "总览", hint: "今日节奏" },
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
      <aside className="bg-soft-meadow px-6 py-8 lg:min-h-screen">
        <LogoLockup />
        <nav className="mt-10 space-y-2">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-[1440px] px-[22px] py-3 ${
                  active ? "bg-canvas font-semibold text-deep-ink" : "text-deep-ink hover:bg-canvas/70"
                }`}
              >
                <span className="block text-[16px] font-medium">{item.label}</span>
                <span className="block text-[10px] font-medium uppercase tracking-[-0.02em] text-slate">
                  {item.hint}
                </span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-12 border-t border-charcoal/20 pt-6 text-body-sm">
          <p className="font-medium text-deep-ink">{user?.name ?? "加载中…"}</p>
          <p className="mt-1 text-slate">{user?.role === "admin" ? "管理员" : "成员"}</p>
          <button type="button" onClick={logout} className="mt-3 font-medium text-deep-ink underline-offset-4 hover:underline">
            退出登录
          </button>
        </div>
      </aside>
      <div>
        <main className="mx-auto w-full max-w-[1200px] px-6 py-10 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
