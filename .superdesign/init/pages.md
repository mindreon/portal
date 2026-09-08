# Page dependency trees

## / (Workbench / Home)

Entry: `apps/web/src/app/page.tsx`

Dependencies:
- `apps/web/src/components/app-shell.tsx`
  - `apps/web/src/components/breadcrumbs.tsx`
    - `apps/web/src/lib/modules.ts`
  - `apps/web/src/components/logo.tsx`
  - `apps/web/src/components/search-palette.tsx`
    - `apps/web/src/lib/api.ts`
    - `apps/web/src/lib/current-user.tsx`
    - `apps/web/src/lib/modules.ts`
    - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/api.ts`
  - `apps/web/src/lib/current-user.tsx`
  - `apps/web/src/lib/modules.ts`
- `apps/web/src/components/ui.tsx` (PageHeader, TextLink)
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/current-user.tsx`
- `apps/web/src/lib/types.ts`
- `apps/web/src/app/globals.css`
- `apps/web/src/app/layout.tsx`

Rendered branch (desktop, user with both modules): AppShell workbench nav + PageHeader (eyebrow Workbench, title 工作台) + 2-col module cards (eyebrow = English hint, heading = Chinese name, summary, “进入 →”) + 3 StatCards + 2 RecentLists.

## /login

Entry: `apps/web/src/app/login/page.tsx`
- `apps/web/src/components/logo.tsx`
- `apps/web/src/components/ui.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/current-user.tsx`
- `apps/web/src/lib/types.ts`

## /contracts

Entry: `apps/web/src/app/contracts/page.tsx`
- `apps/web/src/app/contracts/layout.tsx`
  - `apps/web/src/components/app-shell.tsx` (same tree as /)
- `apps/web/src/components/pinned-table.tsx`
- `apps/web/src/components/status-badge.tsx`
- `apps/web/src/components/ui.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/types.ts`

## /invoices

Entry: `apps/web/src/app/invoices/page.tsx`
- `apps/web/src/components/app-shell.tsx`
- `apps/web/src/components/pinned-table.tsx`
- `apps/web/src/components/status-badge.tsx`
- `apps/web/src/components/ui.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/types.ts`

## /settings/access

Entry: `apps/web/src/app/settings/access/page.tsx`
- `apps/web/src/app/settings/layout.tsx`
- `apps/web/src/components/app-shell.tsx`
- `apps/web/src/components/pinned-table.tsx`
- `apps/web/src/components/ui.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/current-user.tsx`
- `apps/web/src/lib/modules.ts`
- `apps/web/src/lib/types.ts`

## /contracts/payments

Entry: `apps/web/src/app/contracts/payments/page.tsx`
- `apps/web/src/components/app-shell.tsx`
- `apps/web/src/components/pinned-table.tsx`
- `apps/web/src/components/ui.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/types.ts`
