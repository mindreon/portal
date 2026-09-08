# Routes

Framework: Next.js App Router (`apps/web/src/app`). Logged-in pages wrap themselves in `AppShell`. Login is standalone.

| URL | File | Layout | Summary |
| --- | --- | --- | --- |
| `/login` | `apps/web/src/app/login/page.tsx` | none | Centered card: LogoMark, “Portal · Internal”, display title 欢迎回来, Feishu + optional dev login |
| `/` | `apps/web/src/app/page.tsx` | AppShell | Workbench: PageHeader Workbench/工作台, 2-col module cards, 3-col stats, recent lists |
| `/contracts` | `apps/web/src/app/contracts/page.tsx` | AppShell + contracts/layout | Contract list: stats, filter form, pinned table |
| `/contracts/new` | `apps/web/src/app/contracts/new/page.tsx` | same | Upload PDF/zip or switch to manual editor |
| `/contracts/import` | `apps/web/src/app/contracts/import/page.tsx` | same | Import helper |
| `/contracts/payments` | `apps/web/src/app/contracts/payments/page.tsx` | same | Collection rows table |
| `/contracts/[id]` | `apps/web/src/app/contracts/[id]/page.tsx` | same | ContractWorkspace tabs: fields / files / invoices / payments |
| `/invoices` | `apps/web/src/app/invoices/page.tsx` | AppShell | Invoice list table |
| `/invoices/new` | `apps/web/src/app/invoices/new/page.tsx` | AppShell | InvoiceEditor form |
| `/invoices/[id]` | `apps/web/src/app/invoices/[id]/page.tsx` | AppShell | InvoiceEditor for existing |
| `/settings/access` | `apps/web/src/app/settings/access/page.tsx` | AppShell + settings/layout | Admin user/module checkboxes |

Module registry (`apps/web/src/lib/modules.ts`):

- contracts: name 合同, hint Contracts, summary 立约、履约、归档。和发票分开走。 features 全部合同 / 回款
- invoices: name 发票, hint Invoices, summary 开具、收款、作废。需要时再挂合同。 features 全部发票 / 新建发票
- settings (admin only, not a workbench card): name 权限, hint Access

Workbench `/` is the design target for this request.
