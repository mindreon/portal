"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
    <div className="relative min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="relative z-10 border-b border-[var(--line)] px-5 py-6 lg:border-b-0 lg:border-r">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-2xl bg-[var(--mint)] text-sm font-black text-[#06241b] shadow-[0_0_20px_var(--glow-mint)]">
            P
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--muted)]">AI Lab Ops</p>
            <h1 className="text-xl font-semibold">Portal</h1>
          </div>
        </div>
        <nav className="space-y-1.5">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-2xl px-3 py-2.5 ${
                  active
                    ? "bg-white/10 text-white shadow-[inset_0_0_0_1px_rgba(61,255,200,0.28)]"
                    : "text-[var(--muted)] hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="block text-[15px] font-medium">{item.label}</span>
                <span className="block text-[11px] text-[var(--muted)]">{item.hint}</span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-10 border-t border-[var(--line)] pt-4 text-sm">
          <p className="font-medium">{user?.name ?? "加载中…"}</p>
          <p className="mt-1 text-[var(--muted)]">{user?.role === "admin" ? "管理员" : "成员"}</p>
          <button
            type="button"
            onClick={logout}
            className="mt-3 text-[var(--mint)] underline-offset-4 hover:underline"
          >
            退出登录
          </button>
        </div>
      </aside>
      <div className="relative z-10">
        <main className="mx-auto w-full max-w-5xl px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
