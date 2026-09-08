# Shared layouts

## Root layout — `apps/web/src/app/layout.tsx`

Wraps the whole app with Geist + CurrentUserProvider. No chrome.

```tsx
import type { Metadata } from "next";
import { Geist } from "next/font/google";

import { CurrentUserProvider } from "@/lib/current-user";
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
      <body className={`${geist.variable} ${geist.className} antialiased`}>
        <CurrentUserProvider>{children}</CurrentUserProvider>
      </body>
    </html>
  );
}
```

## AppShell — `apps/web/src/components/app-shell.tsx`

Primary chrome for every logged-in page.

Desktop (`lg+`): two-column grid. Left sidebar 264px, `bg-surface-alt`, no divider line. Right: breadcrumbs + search header, then `max-w-[1280px]` main.

**Workbench nav (pathname `/`):** stacked NavLinks:
- 工作台 (selected: white paper rounded 18px) with hint “全部模块”
- 合同 with uppercase hint “Contracts”
- 发票 with uppercase hint “Invoices”
Footer: user name, role (管理员/成员), 权限管理 (admin), 退出登录 underline.

**Inside a module:** “全部模块” back link, module English hint as eyebrow, Chinese module name, then feature links.

Mobile (`<lg`): logo + 退出, then horizontal ChipLinks (active = black fill white text).

```tsx
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { LogoLockup } from "@/components/logo";
import { SearchPalette } from "@/components/search-palette";
import { api } from "@/lib/api";
import { useCurrentUser } from "@/lib/current-user";
import { isFeatureActive, moduleByPath } from "@/lib/modules";

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

function ForbiddenNotice({ name }: { name: string }) {
  return (
    <div className="ui-card max-w-xl p-8">
      <p className="eyebrow">403</p>
      <h2 className="heading mt-2">没有访问权限</h2>
      <p className="mt-3 text-body text-mid-gray">
        你的账号还不能进入「{name}」。需要开通的话，请让管理员打开左下角的「权限管理」，给对应模块打勾。
      </p>
      <Link href="/" className="ui-btn ui-btn-primary mt-6 inline-flex">
        返回工作台
      </Link>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, ready, modules, canAccess } = useCurrentUser();
  const current = moduleByPath(pathname);
  const forbidden = Boolean(ready && current && !canAccess(current.id));
  const navModule = forbidden ? null : current;

  async function logout() {
    await api("/api/v1/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[264px_minmax(0,1fr)]">
      <aside className="hidden flex-col bg-surface-alt px-6 py-8 pb-20 lg:flex lg:min-h-screen">
        <Link href="/" className="inline-block">
          <LogoLockup />
        </Link>

        {navModule ? (
          <div className="mt-10 flex-1">
            <Link href="/" className="text-body text-mid-gray hover:text-ink">
              全部模块
            </Link>
            <p className="eyebrow mt-6">{navModule.hint}</p>
            <p className="mt-2 text-[16px] font-semibold tracking-[-0.4px] text-ink">{navModule.name}</p>
            <nav className="mt-5 space-y-1.5">
              {navModule.features.map((feature) => (
                <NavLink
                  key={feature.href}
                  href={feature.href}
                  label={feature.label}
                  hint={feature.hint}
                  active={isFeatureActive(pathname, feature, navModule.features)}
                />
              ))}
            </nav>
          </div>
        ) : (
          <nav className="mt-10 flex-1 space-y-1.5">
            <NavLink href="/" label="工作台" hint="全部模块" active={pathname === "/"} />
            {modules.map((item) => (
              <NavLink key={item.id} href={item.href} label={item.name} hint={item.hint} active={false} />
            ))}
          </nav>
        )}

        <div className="mt-auto pt-10 text-body">
          <p className="font-medium text-ink">{user?.name ?? "加载中…"}</p>
          <p className="mt-1.5 text-mid-gray">{user?.role === "admin" ? "管理员" : "成员"}</p>
          {user?.role === "admin" ? (
            <Link
              href="/settings/access"
              className={`mt-3 -mx-3.5 block rounded-[18px] px-3.5 py-2.5 text-[14px] font-medium ${
                pathname.startsWith("/settings") ? "bg-paper text-ink" : "text-ink hover:bg-paper"
              }`}
            >
              权限管理
            </Link>
          ) : null}
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
          {navModule
            ? navModule.features.map((feature) => (
                <ChipLink
                  key={feature.href}
                  href={feature.href}
                  label={feature.label}
                  active={isFeatureActive(pathname, feature, navModule.features)}
                />
              ))
            : (
                <>
                  {modules.map((item) => <ChipLink key={item.id} href={item.href} label={item.name} active={false} />)}
                  {user?.role === "admin" ? <ChipLink href="/settings/access" label="权限" active={false} /> : null}
                </>
              )}
        </nav>
        <header className="flex flex-wrap items-center justify-between gap-4 px-6 py-5 sm:px-10">
          <Breadcrumbs />
          <SearchPalette />
        </header>
        <main className="mx-auto w-full max-w-[1280px] flex-1 px-6 pb-12 sm:px-10">
          {forbidden && current ? <ForbiddenNotice name={current.name} /> : children}
        </main>
      </div>
    </div>
  );
}
```

## Module gate layouts

- `apps/web/src/app/contracts/layout.tsx` — if no contracts access, render empty AppShell (ForbiddenNotice comes from AppShell).
- `apps/web/src/app/settings/layout.tsx` — non-admin gets empty AppShell.

Login page has no AppShell.
