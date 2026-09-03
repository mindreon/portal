"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";

const NAV = [
  { href: "/", label: "总览" },
  { href: "/contracts", label: "合同" },
  { href: "/invoices", label: "发票" },
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
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="bg-[var(--navy)] text-[#f6efe3] px-5 py-6">
        <div className="mb-8">
          <p className="text-xs tracking-[0.24em] uppercase text-[#d7b27a]">内部系统</p>
          <h1 className="mt-1 text-2xl font-semibold">Portal</h1>
        </div>
        <nav className="space-y-1">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-md px-3 py-2 text-[15px] ${
                  active ? "bg-[#2a4d73] text-white" : "text-[#d7e2ee] hover:bg-[#214263]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-10 border-t border-white/15 pt-4 text-sm">
          <p>{user?.name ?? "加载中…"}</p>
          <p className="mt-1 text-[#b9c7d6]">{user?.role === "admin" ? "管理员" : "成员"}</p>
          <button
            type="button"
            onClick={logout}
            className="mt-3 text-[#d7b27a] underline-offset-4 hover:underline"
          >
            退出登录
          </button>
        </div>
      </aside>
      <div>
        <main className="mx-auto w-full max-w-5xl px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
