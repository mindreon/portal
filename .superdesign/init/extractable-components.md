# Extractable components

## AppShell
- Source: `apps/web/src/components/app-shell.tsx`
- Category: layout
- Description: Desktop sidebar + mobile chips + breadcrumbs/search header wrapping page content
- Extractable props: activeItem (string, default: "workbench"), userName (string, default: "本地管理员"), isAdmin (boolean, default: true)
- Hardcoded: LogoLockup, nav labels 工作台/合同/发票, English hints 全部模块/Contracts/Invoices, 权限管理, 退出登录, rounded-[18px] paper active state, no icons

## LogoLockup
- Source: `apps/web/src/components/logo.tsx`
- Category: layout
- Description: 28px black rounded-square P mark plus Internal / Portal text
- Extractable props: none
- Hardcoded: SVG mark, “Internal”, “Portal”

## PageHeader
- Source: `apps/web/src/components/ui.tsx`
- Category: basic
- Description: Eyebrow + heading + description + optional action
- Extractable props: eyebrow (string, default: "Workbench"), title (string, default: "工作台"), description (string, default: "")
- Hardcoded: .eyebrow uppercase tracking, .heading 30px

## SearchPalette
- Source: `apps/web/src/components/search-palette.tsx`
- Category: layout
- Description: Header search trigger and command overlay
- Extractable props: none for static preview
- Hardcoded: “搜索模块或记录…”, ⌘K, overlay styles

## Breadcrumbs
- Source: `apps/web/src/components/breadcrumbs.tsx`
- Category: layout
- Description: Workbench › module › feature path
- Extractable props: none (path-derived)
- Hardcoded: 12px chevron SVG

## StatusBadge
- Source: `apps/web/src/components/status-badge.tsx`
- Category: basic
- Description: Monochrome status pill
- Extractable props: value (string, default: "active"), kind (string, default: "contract")
- Hardcoded: tone classes, 18px radius

Skip Button/Input/Card — they are CSS classes, not React components.
