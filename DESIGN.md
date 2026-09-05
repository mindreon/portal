# Portal — Design System

> 风格来源：**Ui — Style Reference**  
> clinical blueprint on frosted paper

**Theme:** light  
**产品：** Portal 内部业务系统（合同、发票为两个独立模块）  
**本文件是前端视觉的唯一依据。** 改颜色、字体、圆角之前先改这里。

---

## 1. 品牌语气

shadcn/ui 式的单色工作台：纯白卡片、偏暖的浅灰画布、大圆角卡片靠发丝描边浮起来。界面几乎全是无彩色——黑字、白面、灰辅助——**唯一的红色 `#e7000b` 只留给删除和错误**。字体用 Geist 的几何中性，大标题字距收得很紧，读起来像开发者基础设施，不是消费级产品。

**对 Portal 的白话版：**

- 没有黄按钮、没有花园色块、没有衬线标题。
- 主操作是黑底白字；取消/次要是浅灰底；删除是红字。
- 合同和发票共用这套皮肤，但仍是两个独立模块。

---

## 2. Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Canvas | `#f5f5f5` | `--color-canvas` | Page background, muted surface fills, secondary buttons |
| Paper | `#ffffff` | `--color-paper` | Card surfaces, popover backgrounds, primary button fills (text on dark) |
| Surface Alt | `#fafafa` | `--color-surface-alt` | Sidebar background, subtle card variant, input resting state companion |
| Ink | `#0a0a0a` | `--color-ink` | Primary text, headings, button labels, icon strokes |
| Ink Soft | `#171717` | `--color-ink-soft` | Filled button backgrounds, secondary text on light surfaces |
| Mid Gray | `#737373` | `--color-mid-gray` | Muted body text, placeholder text, helper labels |
| Hairline | `#e5e5e5` | `--color-hairline` | Borders, input outlines, card edges, badge outlines |
| Ember | `#e7000b` | `--color-ember` | Destructive / error only — never decoration or status “success” |

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
**Input focus:** 1px `#e5e5e5` ring, no offset

**Layout:** max-width 1280px · sidebar 264px · page padding 40px · card padding 24px · control gap 12px · section gap 32px  
**Controls:** button/input height 40px · input padding 10px 14px · table cell 14px 24px

---

## 5. Components → Portal

| 规范 | Portal 用法 |
|------|-------------|
| Primary filled `#0a0a0a` / `#fafafa` | 登录、新建、保存 |
| Secondary ghost `#f5f5f5` | 返回、次要动作（飞书已开时的开发登录） |
| Outline | 卡片内的第三级动作 |
| Card 白底 + hairline + 轻阴影 | 工作台统计、列表、表单 |
| Input 灰底无边，focus 发丝描边 | 全部表单 |
| Badge solid / soft | 状态：履约中/已开具用 solid；草稿用 soft |
| Sidebar `#fafafa` | 左侧导航，不要再画分割线 |
| Breadcrumb | 顶栏层级路径：分隔符 `#737373`，当前段 `#0a0a0a` |
| Search trigger | 顶栏灰底胶囊，右侧 `⌘K`，打开命令面板 |
| Destructive `#e7000b` | 仅「删除」 |

合同 `/contracts`、发票 `/invoices` 保持独立。两边主按钮都是黑底，不再用双彩色编码。

---

## 5.1 多模块交互（工作台进房间）

模块会越来越多，每个模块内部还有子功能。**不要把所有模块平铺在同一条侧栏里。**

可以想成一栋办公楼：

1. **工作台 `/`**：大厅。用卡片进入某个模块，也可以看今日数字。
2. **进入模块后**：侧栏只显示这个模块的子功能（例如合同里的「全部合同 / 新建合同」）。左上角「全部模块」回到大厅。
3. **跨模块**：默认不相通。要从发票跳到某份合同，用页面上的明确链接，或顶栏 `⌘K`。
4. **侧栏只两层**：模块 → 子功能。第三层用页签或页面分区，不要再往侧栏加缩进。
5. **新模块只改一处**：`apps/web/src/lib/modules.ts`。侧栏、工作台格子、面包屑、搜索捷径都读这张表。

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

- Use `#0a0a0a` on `#ffffff` context for filled buttons — dark inversion is the only primary treatment
- 18px radius on buttons, inputs, badges; 24px only on cards
- Display headlines 48px/600 with -0.05em tracking on the login title; inner pages use 30px heading
- Reserve `#e7000b` exclusively for destructive / error
- Keep the 1px hairline on cards
- Surface stack: canvas `#f5f5f5` → sidebar `#fafafa` → paper `#ffffff`

### Don't

- No yellow, green, fuchsia, navy-violet, or serif headlines
- No decorative blobs or illustrations
- No gradients or colored shadows
- No body text below 14px
- No two identical filled black buttons in one row without a ghost sibling

---

## 7. Quick Start

```css
:root {
  --color-canvas: #f5f5f5;
  --color-paper: #ffffff;
  --color-surface-alt: #fafafa;
  --color-ink: #0a0a0a;
  --color-ink-soft: #171717;
  --color-mid-gray: #737373;
  --color-hairline: #e5e5e5;
  --color-ember: #e7000b;
  --font-geist: "Geist", ui-sans-serif, system-ui, sans-serif;
  --radius-cards: 24px;
  --radius-buttons: 18px;
  --shadow-subtle: 0 0 0 1px rgba(23, 23, 23, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  --page-max-width: 1280px;
}
```
