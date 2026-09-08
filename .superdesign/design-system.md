# Portal Design System

> Source of truth for Superdesign. Current product UI is the monochrome workbench in `DESIGN.md`.

**Product:** Portal — 公司内部业务系统  
**Audience:** 内部同事（管理员 + 普通成员），中文界面  
**Platform:** Desktop-first web (sidebar at ≥1024px, chips below)  
**Theme:** light

## Product context & JTBD

合同和发票是两间独立房间。工作台 `/` 是大厅：用卡片进房间，看今日数字和最近记录。侧栏在大厅列出全部模块；进入房间后侧栏只显示该房间子功能。权限由管理员在「权限管理」勾选。

Key pages: `/` 工作台, `/contracts`, `/invoices`, `/settings/access`, `/login`.

## Branding & styling (current live UI)

shadcn/ui 式单色工作台：纯白卡片、浅灰画布 `#f5f5f5`、大圆角 24px 卡片靠发丝描边浮起来。几乎全是无彩色——黑字、白面、灰辅助。**唯一红色 `#e7000b` 只留给删除和错误。**

Font: Geist 400/500/600 + PingFang SC / Noto Sans SC. Headings tight tracking. Body 14px.

### Colors

| Token | Value | Role |
| --- | --- | --- |
| Canvas | `#f5f5f5` | Page, muted fills, secondary buttons |
| Paper | `#ffffff` | Cards, active nav item |
| Surface Alt | `#fafafa` | Sidebar, table header |
| Ink | `#0a0a0a` | Text, primary button |
| Ink Soft | `#171717` | Solid badges |
| Mid Gray | `#737373` | Muted text, English eyebrows |
| Hairline | `#e5e5e5` | Borders |
| Ember | `#e7000b` | Destructive only |

### Type

- `.eyebrow`: 12px / 500 / 0.6px / uppercase / mid-gray — used for English labels (WORKBENCH, CONTRACTS, INVOICES) next to Chinese titles
- `.heading`: 30px / 600 / -0.75px
- `.heading-sm`: 24px / 600
- `.heading-display`: 48px login only
- Nav item: 14px Chinese + 12px uppercase English hint

### Shape & elevation

- Cards 24px radius, 1px hairline + `--shadow-subtle`
- Buttons/inputs/nav pills 18px, height 40px
- Nested 10px
- Sidebar 264px, no divider
- Content max 1280px, padding 24–40px

### Components

- Primary button: ink fill, `#fafafa` text
- Secondary: canvas fill
- Sidebar active: paper white rounded 18px, no icon
- Logo: 28×28 black rounded-square with white “P” path; lockup “Internal” / “Portal”
- Status badges: grayscale pills only
- Search: canvas capsule + `⌘K`

### Layout (Workbench)

Left: LogoLockup, then 工作台 (active) with hint 全部模块, 合同 + CONTRACTS, 发票 + INVOICES. Footer: name, 管理员, 权限管理, 退出登录.

Right header: breadcrumb “工作台” + search trigger.

Main: eyebrow WORKBENCH, heading 工作台, gray description. Then 2-col white module cards (English eyebrow, Chinese title, summary, “进入 →”). Then 3-col stats. Then recent lists.

**No icons anywhere except the logo mark and breadcrumb chevron.**

## Motion

None. Instant hover background changes only.

## Constraints for pixel-perfect reproduction

- Keep Geist, black/white/gray palette, 24px cards, 18px controls
- Keep English uppercase eyebrows and sidebar hints exactly as in source
- Do not invent colored status, illustrations, or extra chrome
- Do not replace the logo with initials or a different mark
