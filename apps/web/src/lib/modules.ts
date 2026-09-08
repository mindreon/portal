import type { CurrentUser } from "@/lib/types";

/**
 * 业务模块注册表。
 *
 * 新模块只在这里加一条：前端侧栏、工作台格子、面包屑、⌘K 捷径都会跟着出现。
 * 侧栏最多两层——模块 → 子功能。第三层用页面里的页签，不要再往侧栏里塞。
 *
 * 谁能看见哪个模块，不在这里写死，而以后端 /auth/me 返回的 modules 为准。
 */
export type ModuleFeature = {
  href: string;
  label: string;
  hint?: string;
};

export type BusinessModule = {
  id: string;
  name: string;
  href: string;
  summary: string;
  features: ModuleFeature[];
};

export const MODULES: BusinessModule[] = [
  {
    id: "contracts",
    name: "合同",
    href: "/contracts",
    summary: "立约、履约、归档。和发票分开走。",
    features: [
      { href: "/contracts", label: "全部合同" },
      { href: "/contracts/payments", label: "回款" },
    ],
  },
  {
    id: "invoices",
    name: "发票",
    href: "/invoices",
    summary: "开具、收款、作废。需要时再挂合同。",
    features: [
      { href: "/invoices", label: "全部发票" },
      { href: "/invoices/new", label: "新建发票" },
    ],
  },
];

/**
 * 权限管理不是业务房间，不出现在工作台卡片里。
 * 只有管理员能进：给每个同事勾选合同 / 发票。
 */
export const SETTINGS_MODULE: BusinessModule = {
  id: "settings",
  name: "权限",
  href: "/settings/access",
  summary: "给每个人勾选能进的房间。",
  features: [{ href: "/settings/access", label: "人员权限" }],
};

export function moduleByPath(pathname: string): BusinessModule | null {
  if (pathname === SETTINGS_MODULE.href || pathname.startsWith("/settings/")) {
    return SETTINGS_MODULE;
  }
  return MODULES.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`)) ?? null;
}

export function isFeatureActive(pathname: string, feature: ModuleFeature, siblings: ModuleFeature[]) {
  if (pathname === feature.href) return true;
  if (!pathname.startsWith(`${feature.href}/`)) return false;
  return !siblings.some(
    (other) =>
      other.href !== feature.href &&
      (pathname === other.href || pathname.startsWith(`${other.href}/`)),
  );
}

export function featureLabel(pathname: string, module: BusinessModule) {
  const exact = module.features.find((item) => pathname === item.href);
  if (exact) return exact.label;
  if (pathname.includes("/payments")) return "回款";
  if (pathname.includes("/import") || pathname.endsWith("/new")) return "新建合同";
  return "详情";
}

export type Crumb = { href?: string; label: string };

export function crumbsFor(pathname: string): Crumb[] {
  if (pathname === "/") return [{ label: "工作台" }];
  const current = moduleByPath(pathname);
  if (!current) return [{ href: "/", label: "工作台" }];
  if (pathname === current.href) {
    return [{ href: "/", label: "工作台" }, { label: current.name }];
  }
  return [{ href: "/", label: "工作台" }, { href: current.href, label: current.name }, { label: featureLabel(pathname, current) }];
}

export function modulesFor(user: CurrentUser | null): BusinessModule[] {
  if (!user) return [];
  return MODULES.filter((item) => (user.modules ?? []).includes(item.id));
}

export function canAccessModule(user: CurrentUser | null, moduleId: string) {
  if (moduleId === SETTINGS_MODULE.id) return user?.role === "admin";
  return Boolean(user?.modules?.includes(moduleId));
}

export function searchShortcuts(user: CurrentUser | null) {
  const visible = modulesFor(user);
  const shortcuts = [
    { href: "/", title: "工作台", meta: "全部模块" },
    ...visible.flatMap((item) => [
      { href: item.href, title: item.name, meta: "独立模块" },
      ...item.features
        .filter((feature) => feature.href !== item.href)
        .map((feature) => ({ href: feature.href, title: feature.label, meta: item.name })),
    ]),
  ];
  if (user?.role === "admin") {
    shortcuts.push({ href: SETTINGS_MODULE.href, title: "权限管理", meta: "给同事勾选模块" });
  }
  return shortcuts;
}
