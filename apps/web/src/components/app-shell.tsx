"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { Icon, moduleIcon, type IconName } from "@/components/icons";
import { LogoLockup } from "@/components/logo";
import { SearchPalette } from "@/components/search-palette";
import { api } from "@/lib/api";
import { useCurrentUser } from "@/lib/current-user";
import { isFeatureActive, moduleByPath } from "@/lib/modules";

function NavLink({
  href,
  label,
  hint,
  icon,
  active,
}: {
  href: string;
  label: string;
  hint?: string;
  icon?: IconName;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-[18px] px-3.5 py-2.5 ${
        active ? "bg-brand-soft font-medium text-brand" : "text-ink hover:bg-canvas"
      }`}
    >
      {icon ? <Icon name={icon} className={active ? "text-brand" : "text-mid-gray"} /> : null}
      <span className="min-w-0">
        <span className="block text-[14px]">{label}</span>
        {hint ? <span className="mt-0.5 block text-[12px] text-mid-gray">{hint}</span> : null}
      </span>
    </Link>
  );
}

function ChipLink({ href, label, active }: { href: string; label: string; active: boolean }) {
  return (
    <Link
      href={href}
      className={`shrink-0 rounded-[18px] px-3.5 py-2 text-[14px] ${active ? "bg-brand font-medium text-paper" : "bg-canvas text-ink"}`}
    >
      {label}
    </Link>
  );
}

function ForbiddenNotice({ name }: { name: string }) {
  return (
    <div className="ui-card max-w-xl p-8">
      <p className="text-[12px] font-medium text-mid-gray">没有权限</p>
      <h2 className="heading mt-2">进不了「{name}」</h2>
      <p className="mt-3 text-body text-mid-gray">
        你的账号还不能进入这个房间。需要开通的话，请让管理员打开左下角的「权限管理」，给对应模块打勾。
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
  // 没权限时不要展开合同子菜单，否则等于把入口又露出来了。
  const navModule = forbidden ? null : current;

  async function logout() {
    await api("/api/v1/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[264px_minmax(0,1fr)]">
      <aside className="hidden flex-col border-r border-sidebar-line bg-paper px-6 py-8 pb-20 lg:flex lg:min-h-screen">
        <Link href="/" className="inline-block">
          <LogoLockup />
        </Link>

        {navModule ? (
          <div className="mt-10 flex-1">
            <Link href="/" className="text-body text-mid-gray hover:text-ink">
              全部模块
            </Link>
            <p className="mt-6 flex items-center gap-2 text-[16px] font-semibold tracking-[-0.4px] text-ink">
              <Icon name={moduleIcon(navModule.id)} className="text-brand" />
              {navModule.name}
            </p>
            <nav className="mt-5 space-y-1.5">
              {navModule.features.map((feature) => (
                <NavLink
                  key={feature.href}
                  href={feature.href}
                  label={feature.label}
                  active={isFeatureActive(pathname, feature, navModule.features)}
                />
              ))}
            </nav>
          </div>
        ) : (
          <nav className="mt-10 flex-1 space-y-1.5">
            <NavLink
              href="/"
              label="工作台"
              hint="全部模块"
              icon="layout-dashboard"
              active={pathname === "/"}
            />
            {modules.map((item) => (
              <NavLink
                key={item.id}
                href={item.href}
                label={item.name}
                icon={moduleIcon(item.id)}
                active={false}
              />
            ))}
          </nav>
        )}

        <div className="mt-auto pt-10 text-body">
          <p className="font-medium text-ink">{user?.name ?? "加载中…"}</p>
          <p className="mt-1.5 text-mid-gray">{user?.role === "admin" ? "管理员" : "成员"}</p>
          {user?.role === "admin" ? (
            <Link
              href="/settings/access"
              className={`mt-3 -mx-3.5 flex items-center gap-2 rounded-[18px] px-3.5 py-2.5 text-[14px] font-medium ${
                pathname.startsWith("/settings") ? "bg-brand-soft text-brand" : "text-ink hover:bg-canvas"
              }`}
            >
              <Icon name="shield" size={18} className={pathname.startsWith("/settings") ? "text-brand" : "text-mid-gray"} />
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
