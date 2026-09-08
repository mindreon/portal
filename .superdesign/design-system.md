# Portal Design System

> Iteration target for the workbench refresh. Keep the information architecture; stop looking like a grayscale wireframe.

**Product:** Portal — 公司内部业务系统  
**Audience:** 内部同事（管理员 + 普通成员），中文界面  
**Platform:** Desktop-first web  
**Theme:** light

## Product context & JTBD

合同和发票是两间独立房间。工作台 `/` 是大厅：用卡片进房间，看今日数字和最近记录。侧栏在大厅列出全部模块。权限由管理员在「权限管理」勾选。

## Visual direction (refresh)

Soft **product workspace**, not a landing page and not a wireframe.

- Canvas is a cool slate-blue wash, not dead gray.
- Sidebar is white with a hairline edge; the active item uses a pale blue well and a colored icon.
- Every module has a recognizable icon. Cards get a 40px rounded icon tile.
- Chinese titles stand alone. **Never** stack an English uppercase duplicate (`WORKBENCH`, `CONTRACTS`, `INVOICES`) above or below the Chinese name.
- Keep Geist / Noto Sans SC, 24px cards, 18px controls, and the real Portal logo.

## Colors

| Token | Value | Role |
| --- | --- | --- |
| Canvas | `#F1F4F8` | Page background |
| Paper | `#FFFFFF` | Cards, sidebar |
| Sidebar line | `#E8ECF1` | Sidebar right border |
| Ink | `#0F172A` | Headings, primary text (slate-900) |
| Mid | `#64748B` | Secondary text (slate-500) |
| Hairline | `#E2E8F0` | Card borders |
| Brand | `#2563EB` | Active nav, links, workbench / contract icons |
| Brand soft | `#EFF4FF` | Active nav background |
| Teal | `#0F766E` | Invoice icon |
| Teal soft | `#CCFBF1` | Invoice icon well |
| Blue soft | `#DBEAFE` | Contract icon well |
| Ember | `#e7000b` | Destructive / error only |

Primary filled button stays ink (`#0F172A` on white text). Do not invent pink, purple, neon, or serif headlines. No full-page gradients. No glassmorphism blobs.

## Typography

- Family: Geist, PingFang SC, Noto Sans SC. Weights 400 / 500 / 600.
- Body 14px. Page title 30px/600, tight tracking. Card titles 20–24px/600.
- Helper text 13–14px slate-500. **No 12px uppercase English eyebrows** next to Chinese titles.
- Logo lockup may keep “Internal” / “Portal” — that is the product name, not a duplicate of 工作台.

## Icons

Use `iconify-icon` (Lucide set). 20px stroke in the sidebar, 22px in module tiles.

| Place | Icon |
| --- | --- |
| 工作台 | `lucide:layout-dashboard` |
| 合同 | `lucide:file-text` |
| 发票 | `lucide:receipt` |
| 权限管理 | `lucide:shield` |
| 搜索 | `lucide:search` |
| 进入 | `lucide:arrow-right` |

Icon tiles on module cards: 44×44, radius 14px, tinted well + brand-colored icon.

## Shape

- Cards 24px, 1px hairline, light shadow
- Nav items 14px radius, 8px vertical padding, icon + label in a row
- Buttons / search 18px height 40px
- Sidebar 264px

## Workbench layout (after refresh)

Left: logo lockup (exact Brand Asset logo, never initials/emoji/generic mark) → nav rows with icon + Chinese label only. 工作台 shows a small Chinese helper “全部模块” (not English). Footer: name, 管理员, 权限管理 with shield icon, 退出登录.

Right header: breadcrumb 工作台 + search with search icon and ⌘K.

Main: **no Workbench eyebrow**. Heading 工作台 + description. Two module cards with icon tile, Chinese title, summary, “进入” + arrow icon. Three stats with a small matching icon. Two recent lists unchanged in content.

## Motion

Hover: card border/shadow slightly stronger; nav well appears. No looping animation.

## Constraints

- Use ONLY these fonts, colors, spacing, and icon choices
- Keep the real Portal logo URL in every logo position
- Remove duplicate English labels everywhere except the product lockup “Internal / Portal”
