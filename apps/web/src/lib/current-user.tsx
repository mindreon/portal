"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { canAccessModule, modulesFor } from "@/lib/modules";
import type { BusinessModule } from "@/lib/modules";
import type { CurrentUser } from "@/lib/types";

type CurrentUserState = {
  user: CurrentUser | null;
  ready: boolean;
  modules: BusinessModule[];
  canAccess: (moduleId: string) => boolean;
};

const CurrentUserContext = createContext<CurrentUserState>({
  user: null,
  ready: false,
  modules: [],
  canAccess: () => false,
});

/**
 * 登录用户只拉一次。侧栏、工作台、搜索都读这里的 modules，
 * 避免每个页面自己请求 /auth/me，菜单才不会各画各的。
 */
export function CurrentUserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api<CurrentUser>("/api/v1/auth/me", { skipAuthRedirect: true })
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);

  const value = useMemo<CurrentUserState>(
    () => ({
      user,
      ready,
      modules: modulesFor(user),
      canAccess: (moduleId: string) => canAccessModule(user, moduleId),
    }),
    [user, ready],
  );

  return <CurrentUserContext.Provider value={value}>{children}</CurrentUserContext.Provider>;
}

export function useCurrentUser() {
  return useContext(CurrentUserContext);
}
