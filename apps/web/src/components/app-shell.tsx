"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { LogoLockup } from "@/components/logo";
import { SearchPalette } from "@/components/search-palette";
import { api } from "@/lib/api";
import { isFeatureActive, MODULES, moduleByPath } from "@/lib/modules";
import type { CurrentUser } from "@/lib/types";

function NavLink({
  href,
  label,
  hint,
  active,
}: {
  href: string;
  label: string;
  hint?: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`block rounded-[18px] px-3 py-2 ${active ? "bg-paper font-medium text-ink" : "text-ink hover:bg-paper"}`}
    >
      <span className="block text-[14px]">{label}</span>
      {hint ? <span className="block text-[12px] tracking-[0.6px] text-mid-gray uppercase">{hint}</span> : null}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const current = moduleByPath(pathname);

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
        <Link href="/" className="inline-block">
          <LogoLockup />
        </Link>

        {current ? (
          <div className="mt-8">
            <Link href="/" className="text-body text-mid-gray hover:text-ink">
              全部模块
            </Link>
            <p className="eyebrow mt-5">{current.hint}</p>
            <p className="mt-1 text-[16px] font-semibold tracking-[-0.4px] text-ink">{current.name}</p>
            <nav className="mt-4 space-y-1">
              {current.features.map((feature) => (
                <NavLink
                  key={feature.href}
                  href={feature.href}
                  label={feature.label}
                  hint={feature.hint}
                  active={isFeatureActive(pathname, feature, current.features)}
                />
              ))}
            </nav>
          </div>
        ) : (
          <nav className="mt-8 space-y-1">
            <NavLink href="/" label="工作台" hint="全部模块" active={pathname === "/"} />
            {MODULES.map((item) => (
              <NavLink key={item.id} href={item.href} label={item.name} hint={item.hint} active={false} />
            ))}
          </nav>
        )}

        <div className="mt-10 pt-5 text-body">
          <p className="font-medium text-ink">{user?.name ?? "加载中…"}</p>
          <p className="mt-1 text-mid-gray">{user?.role === "admin" ? "管理员" : "成员"}</p>
          <button type="button" onClick={logout} className="mt-3 font-medium text-ink underline-offset-4 hover:underline">
            退出登录
          </button>
        </div>
      </aside>
      <div>
        <header className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 sm:px-8">
          <Breadcrumbs />
          <SearchPalette />
        </header>
        <main className="mx-auto w-full max-w-[1280px] px-5 pb-8 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
