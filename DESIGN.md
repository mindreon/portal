# Portal — Design System

> 风格来源：浅石板蓝工作台 + 品牌蓝图标  
> 不再用纯黑白线框。

**Theme:** light  
**产品：** Portal 内部业务系统（合同、发票为两个独立模块）  
**本文件是前端视觉的唯一依据。** 改颜色、字体、圆角之前先改这里。

---

## 1. 品牌语气

内部产品工作台：浅石板蓝画布、白卡片、白侧栏带发丝右边线。中文标题单独出现，**不要再叠一层英文大写 label**（Workbench / Contracts / Invoices）。侧栏和模块卡片用 Lucide 线框图标做锚点。主按钮仍是深色填充；品牌蓝 `#2563EB` 只用于选中态、链接和图标。**红色 `#e7000b` 只留给删除和错误。**

**对 Portal 的白话版：**

- 没有黄按钮、没有花园色块、没有衬线标题。
- 主操作是深底白字；取消/次要是浅灰底；删除是红字。
- 合同图标偏蓝，发票图标偏青绿，方便扫一眼区分房间。
- 合同和发票共用这套皮肤，但仍是两个独立模块。

---

## 2. Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Canvas | `#F1F4F8` | `--color-canvas` | Page background, muted fills, secondary buttons |
| Paper | `#ffffff` | `--color-paper` | Cards, sidebar, popovers |
| Surface Alt | `#F8FAFC` | `--color-surface-alt` | Table header |
| Sidebar line | `#E8ECF1` | `--color-sidebar-line` | Sidebar right border |
| Ink | `#0F172A` | `--color-ink` | Primary text, headings, filled buttons |
| Ink Soft | `#1E293B` | `--color-ink-soft` | Solid badges |
| Mid Gray | `#64748B` | `--color-mid-gray` | Muted body, placeholders |
| Hairline | `#E2E8F0` | `--color-hairline` | Card and table borders |
| Brand | `#2563EB` | `--color-brand` | Active nav, workbench / contract icons |
| Brand soft | `#EFF4FF` | `--color-brand-soft` | Active nav well |
| Teal | `#0F766E` | `--color-teal` | Invoice icons |
| Teal soft | `#CCFBF1` | `--color-teal-soft` | Invoice icon well |
| Blue soft | `#DBEAFE` | `--color-blue-soft` | Contract icon well |
| Ember | `#e7000b` | `--color-ember` | Destructive / error only |

---

## 3. Tokens — Typography

### Geist — `--font-geist`

All interface text. Body 14px/400, headings 24–48px/600, buttons 13–14px/500.

- **Substitute:** Inter
- **Weights:** 400, 500, 600
- **OpenType:** `"ss01" on, "cv11" on`

### Type Scale

| Role | Size | Line Height | Letter Spacing | Token |
|------|------|-------------|----------------|-------|
| caption | 12px | 1.33 | 0.6px | `--text-caption` |
| body | 14px | 1.43 | — | `--text-body` |
| body-lg | 16px | 1.5 | — | `--text-body-lg` |
| subheading | 18px | 1.56 | — | `--text-subheading` |
| heading-sm | 24px | 1.33 | -0.6px | `--text-heading-sm` |
| heading | 30px | 1.2 | -0.75px | `--text-heading` |
| heading-lg | 36px | 1.11 | -0.9px | `--text-heading-lg` |
| display | 48px | 1.1 | -2.4px | `--text-display` |

---

## 4. Spacing & Shapes

**Base unit:** 4px · **Density:** comfortable（内部工作台要留出阅读空间，不要挤成仪表盘）

| Name | Value | Token |
|------|-------|-------|
| 4 | 4px | `--spacing-4` |
| 8 | 8px | `--spacing-8` |
| 12 | 12px | `--spacing-12` |
| 16 | 16px | `--spacing-16` |
| 20 | 20px | `--spacing-20` |
| 24 | 24px | `--spacing-24` |
| 32 | 32px | `--spacing-32` |
| 48 | 48px | `--spacing-48` |

| Element | Radius |
|---------|--------|
| cards | 24px |
| buttons / inputs / badges | 18px |
| nested | 10px |
| small | 6px |

**Card elevation:** `0 0 0 1px rgba(23,23,23,0.05), 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px -1px rgba(0,0,0,0.1)`  
**Filled button:** no shadow  
**Input focus:** 1px `#E2E8F0` ring, no offset

**Layout:** max-width 1280px · sidebar 264px · page padding 40px · card padding 24px · control gap 12px · section gap 32px  
**Controls:** button/input height 40px · input padding 10px 14px · table cell 14px 24px  
**Stats:** 金额类数字用 `clamp(24px, 2vw, 30px)`，宽屏四列、中屏两列，避免把卡片撑破

---

## 5. Components → Portal

| 规范 | Portal 用法 |
|------|-------------|
| Primary filled `#0F172A` / `#fafafa` | 登录、新建、保存 |
| Secondary ghost `#F1F4F8` | 返回、次要动作（飞书已开时的开发登录） |
| Outline | 卡片内的第三级动作 |
| Card 白底 + hairline + 轻阴影 | 工作台统计、列表、表单 |
| Input 灰底无边，focus 发丝描边 | 全部表单 |
| Badge solid / soft | 状态：履约中/已开具用 solid；草稿用 soft |
| Sidebar `#ffffff` + `#E8ECF1` 右边线 | 左侧导航，选中项用品牌蓝浅底 |
| 图标 | 工作台 layout-dashboard、合同 file-text、发票 receipt、权限 shield |
| Breadcrumb | 顶栏层级路径：分隔符 `#64748B`，当前段 `#0F172A` |
| Search trigger | 顶栏灰底胶囊，左侧搜索图标，右侧 `⌘K` |
| Destructive `#e7000b` | 仅「删除」 |

合同 `/contracts`、发票 `/invoices` 保持独立。两边主按钮都是深色，不用整页双色编码。页面标题只写中文，不要再加英文 eyebrow。

---

## 5.1 多模块交互（工作台进房间）

模块会越来越多，每个模块内部还有子功能。**不要把所有模块平铺在同一条侧栏里。**

可以想成一栋办公楼：

1. **工作台 `/`**：大厅。用卡片进入某个模块，也可以看今日数字。
2. **进入模块后**：侧栏只显示这个模块的子功能（例如合同里的「全部合同 / 新建合同」）。左上角「全部模块」回到大厅。
3. **跨模块**：默认不相通。要从发票跳到某份合同，用页面上的明确链接，或顶栏 `⌘K`。
4. **侧栏只两层**：模块 → 子功能。第三层用页签或页面分区，不要再往侧栏加缩进。
5. **窄屏**：小于 1024px 时不要把整条侧栏叠在内容上面。顶栏只留 Logo 和退出，下面用横滑 chips 切换工作台 / 子功能。
6. **新模块只改一处**：`apps/web/src/lib/modules.ts`。侧栏、工作台格子、面包屑、搜索捷径都读这张表。

合同房间子功能：全部合同、回款。新建合同在列表右上角，默认上传 PDF，也可以改手工填写。点进某份合同后，用页签看要素 / 附件 / 发票 / 回款。

- 有合同编号：同一编号的多个 PDF 合成一份。
- 没有编号：每个文件单独一份草稿，系统用内部 ID 区分，编号可后补。
- 混入的发票 PDF 生成该合同下的发票草稿。
- 甲、乙都记，并标明我方是甲还是乙（两种都可能）。
- 回款：抽到付款比例就分期；否则一次性一期。

URL 约定：`/[模块]/[子功能]/[id]`，例如 `/contracts/new`、`/invoices/12`。后端同样按模块拆文件：`apps/api/app/modules/<name>.py`。

---

## 6. Do / Don't

### Do

- Use `#0F172A` on `#ffffff` context for filled buttons — dark inversion is the only primary treatment
- Use `#2563EB` for active nav and icons, not for primary buttons
- 18px radius on buttons, inputs, badges; 24px only on cards
- Display headlines 48px/600 with -0.05em tracking on the login title; inner pages use 30px heading
- Reserve `#e7000b` exclusively for destructive / error
- Keep the 1px hairline on cards
- Surface stack: canvas `#F1F4F8` → sidebar/paper `#ffffff` → table header `#F8FAFC`
- Chinese titles stand alone; logo lockup may keep Internal / Portal

### Don't

- No stacked English uppercase duplicates next to Chinese titles (Workbench, Contracts, Invoices)
- No yellow, fuchsia, navy-violet, or serif headlines
- No decorative blobs or illustrations
- No full-page gradients or colored shadows
- No body text below 14px
- No two identical filled dark buttons in one row without a ghost sibling

---

## 7. Quick Start

```css
:root {
  --color-canvas: #F1F4F8;
  --color-paper: #ffffff;
  --color-surface-alt: #F8FAFC;
  --color-ink: #0F172A;
  --color-ink-soft: #1E293B;
  --color-mid-gray: #64748B;
  --color-hairline: #E2E8F0;
  --color-sidebar-line: #E8ECF1;
  --color-brand: #2563EB;
  --color-brand-soft: #EFF4FF;
  --color-teal: #0F766E;
  --color-teal-soft: #CCFBF1;
  --color-blue-soft: #DBEAFE;
  --color-ember: #e7000b;
  --font-geist: "Geist", ui-sans-serif, system-ui, sans-serif;
  --radius-cards: 24px;
  --radius-buttons: 18px;
  --shadow-subtle: 0 0 0 1px rgba(23, 23, 23, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  --page-max-width: 1280px;
}
```
