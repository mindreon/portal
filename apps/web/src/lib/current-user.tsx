"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { canAccessModule, modulesFor } from "@/lib/modules";
import type { BusinessModule } from "@/lib/modules";
import type { CurrentUser } from "@/lib/types";

type CurrentUserState = {
  user: CurrentUser | null;
  ready: boolean;
  modules: BusinessModule[];
  canAccess: (moduleId: string) => boolean;
  reload: () => Promise<void>;
};

const CurrentUserContext = createContext<CurrentUserState>({
  user: null,
  ready: false,
  modules: [],
  canAccess: () => false,
  reload: async () => undefined,
});

/**
 * 登录用户只拉一次。侧栏、工作台、搜索都读这里的 modules，
 * 避免每个页面自己请求 /auth/me，菜单才不会各画各的。
 * 管理员在权限页改了自己的勾选后，会调用 reload() 刷新菜单。
 */
export function CurrentUserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [ready, setReady] = useState(false);

  const reload = useCallback(async () => {
    try {
      const next = await api<CurrentUser>("/api/v1/auth/me", { skipAuthRedirect: true });
      setUser(next);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    reload().finally(() => setReady(true));
  }, [reload]);

  const value = useMemo<CurrentUserState>(
    () => ({
      user,
      ready,
      modules: modulesFor(user),
      canAccess: (moduleId: string) => canAccessModule(user, moduleId),
      reload,
    }),
    [user, ready, reload],
  );

  return <CurrentUserContext.Provider value={value}>{children}</CurrentUserContext.Provider>;
}

export function useCurrentUser() {
  return useContext(CurrentUserContext);
}
