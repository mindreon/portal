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
      className={`block rounded-[18px] px-3.5 py-2.5 ${active ? "bg-paper font-medium text-ink" : "text-ink hover:bg-paper"}`}
    >
      <span className="block text-[14px]">{label}</span>
      {hint ? <span className="mt-0.5 block text-[12px] tracking-[0.6px] text-mid-gray uppercase">{hint}</span> : null}
    </Link>
  );
}

function ChipLink({ href, label, active }: { href: string; label: string; active: boolean }) {
  return (
    <Link
      href={href}
      className={`shrink-0 rounded-[18px] px-3.5 py-2 text-[14px] ${active ? "bg-ink font-medium text-[#fafafa]" : "bg-canvas text-ink"}`}
    >
      {label}
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
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[264px_minmax(0,1fr)]">
      <aside className="hidden flex-col bg-surface-alt px-6 py-8 lg:flex lg:min-h-screen">
        <Link href="/" className="inline-block">
          <LogoLockup />
        </Link>

        {current ? (
          <div className="mt-10 flex-1">
            <Link href="/" className="text-body text-mid-gray hover:text-ink">
              全部模块
            </Link>
            <p className="eyebrow mt-6">{current.hint}</p>
            <p className="mt-2 text-[16px] font-semibold tracking-[-0.4px] text-ink">{current.name}</p>
            <nav className="mt-5 space-y-1.5">
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
          <nav className="mt-10 flex-1 space-y-1.5">
            <NavLink href="/" label="工作台" hint="全部模块" active={pathname === "/"} />
            {MODULES.map((item) => (
              <NavLink key={item.id} href={item.href} label={item.name} hint={item.hint} active={false} />
            ))}
          </nav>
        )}

        <div className="mt-auto pt-10 text-body">
          <p className="font-medium text-ink">{user?.name ?? "加载中…"}</p>
          <p className="mt-1.5 text-mid-gray">{user?.role === "admin" ? "管理员" : "成员"}</p>
          <button type="button" onClick={logout} className="mt-4 font-medium text-ink underline-offset-4 hover:underline">
            退出登录
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <div className="flex items-center justify-between gap-4 px-6 py-4 lg:hidden">
          <Link href="/">
            <LogoLockup />
          </Link>
          <button type="button" onClick={logout} className="text-body font-medium text-ink underline-offset-4 hover:underline">
            退出
          </button>
        </div>
        <nav className="flex gap-2 overflow-x-auto px-6 pb-3 lg:hidden">
          <ChipLink href="/" label="工作台" active={pathname === "/"} />
          {current
            ? current.features.map((feature) => (
                <ChipLink
                  key={feature.href}
                  href={feature.href}
                  label={feature.label}
                  active={isFeatureActive(pathname, feature, current.features)}
                />
              ))
            : MODULES.map((item) => <ChipLink key={item.id} href={item.href} label={item.name} active={false} />)}
        </nav>
        <header className="flex flex-wrap items-center justify-between gap-4 px-6 py-5 sm:px-10">
          <Breadcrumbs />
          <SearchPalette />
        </header>
        <main className="mx-auto w-full max-w-[1280px] flex-1 px-6 pb-12 sm:px-10">{children}</main>
      </div>
    </div>
  );
}
