"use client";

import { AppShell } from "@/components/app-shell";
import { useCurrentUser } from "@/lib/current-user";

/**
 * 合同整棵路由先看权限。没权限就不渲染下面的页面，
 * 避免列表/详情自己的请求打到后端再弹出一串 403。
 */
export default function ContractsLayout({ children }: { children: React.ReactNode }) {
  const { ready, canAccess } = useCurrentUser();

  if (!ready) {
    return (
      <AppShell>
        <p className="text-body text-mid-gray">正在确认权限…</p>
      </AppShell>
    );
  }

  if (!canAccess("contracts")) {
    return (
      <AppShell>
        {null}
      </AppShell>
    );
  }

  return children;
}
