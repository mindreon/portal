"use client";

import { AppShell } from "@/components/app-shell";
import { useCurrentUser } from "@/lib/current-user";

/** 普通员工打不开权限页，避免页面去请求 /users 再收到 403。 */
export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const { ready, user } = useCurrentUser();

  if (!ready) {
    return (
      <AppShell>
        <p className="text-body text-mid-gray">正在确认权限…</p>
      </AppShell>
    );
  }

  if (user?.role !== "admin") {
    return (
      <AppShell>
        {null}
      </AppShell>
    );
  }

  return children;
}
