# Portal — Design System

> 风格来源：**Ditto — Style Reference**  
> Sunlit wildflower compliance atelier. Warm cream surfaces, vivid yellow primary action, deep navy ink, organic color shapes blooming behind the product.

**Theme:** light  
**产品：** Portal 内部业务系统（合同、发票为两个独立模块）  
**本文件是前端视觉的唯一依据。** 改颜色、字体、圆角、按钮之前先改这里，再改代码。

---

## 1. 品牌语气

Ditto / Portal 使用阳光花园式的 SaaS 语言：暖奶油画布、翠绿 / 粉红 / 明黄的有机色块、以及一组自信的字体搭配——标题用暖衬线 **Hedvig Letters**，其余全部用干净的 grotesque **Inter**。结构文字和描边由深紫墨色 `#130e30` 承担；唯一的主操作色是亮黄 `#ffe228`，对比高到像荧光笔。组件保持轻量：胶囊按钮（圆角 1440px）、铺在略带绿调表面 `#eff2e5` 上的宽松卡片、几乎没有阴影。情绪是乐观、好靠近，不是机关公文，也不是冷冰冰的实验室。

**对 Portal 的意思（给你自己看的白话版）：**

- 页面是浅色、偏暖、带一点草地绿，不是上一版的深色霓虹，也不是传统海军蓝公文风。
- 标题像一本认真的书，按钮和表格像一套好用的工具。
- 合同和发票在业务上完全独立；它们共用这套皮肤，但不共用页面、接口或主按钮的位置。

---

## 2. Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Deep Ink | `#130e30` | `--color-deep-ink` | Primary text color, heading ink, card borders, secondary button fills — near-black violet that adds warmth over pure black |
| Hi-Yellow | `#ffe228` | `--color-hi-yellow` | Primary action fill (filled CTA buttons), hero pill backgrounds, accent highlights — bright highlighter yellow with near-black text for maximum contrast |
| Moss Green | `#59e25d` | `--color-moss-green` | Decorative organic shape fill behind hero — warm leaf green used in background blobs, **not UI controls** |
| Fuchsia | `#e261e5` | `--color-fuchsia` | Decorative organic shape fill behind hero — vivid pink used in background blobs, **not UI controls** |
| Slate | `#5f5c6e` | `--color-slate` | Body text, helper copy, muted icons, subtle borders — cool desaturated gray for secondary information |
| Canvas | `#f9fbf2` | `--color-canvas` | Page background, button ghost fills, lightest surface — near-white with slight green-warmth |
| Soft Meadow | `#eff2e5` | `--color-soft-meadow` | Card surfaces, nav background, elevated panels, hero backdrop — green-tinted off-white for soft surface separation |
| Charcoal | `#222222` | `--color-charcoal` | Secondary dark button text and borders, nav dividers — softer than pure black for dark UI elements |
| Onyx | `#000000` | `--color-onyx` | Logo mark, nav text, input borders, fine stroke details — true black for highest-contrast elements |

### 装饰色 vs 界面色（必须守住）

`#59e25d`（Moss Green）和 `#e261e5`（Fuchsia）**只允许**出现在登录页 / 工作台背后的有机色块里。禁止出现在按钮、徽章、标签、图标、状态点、表格高亮等任何可点击或可扫读的控件上。

唯一例外：`#ffe228` 既是装饰色块，也是主 CTA 填充。这是刻意的桥：用户先在氛围里看到黄，再去点黄色按钮。

状态（草稿 / 履约中 / 已开具 / 已收款）用 **Deep Ink、Slate、Hi-Yellow、Soft Meadow** 的深浅组合，不要用绿或粉当状态色。

---

## 3. Tokens — Typography

### Hedvig Letters Serif — `--font-hedvig-letters-serif`

Display and heading serif — all hero/section headlines, used at large sizes with tight letter-spacing. The warm humanist serif is the brand's voice; it gives the product a literary, trustworthy quality instead of a sterile SaaS feel. The 700 weight carries the headlines, while 400 appears in larger pull-quote contexts.

- **Substitute:** DM Serif Display, Source Serif 4, Libre Caslon Text
- **Weights:** 400, 700
- **Sizes:** 22px, 32px, 48px, 64px
- **Line height:** 1.00–1.25
- **Letter spacing:** -0.0100em
- **Portal 用法：** 登录大标题、各页 `h1/h2`（工作台、合同、发票、新建/编辑）。**禁止**用在按钮、表格、表单、导航链接上。

### Inter — `--font-inter`

All UI and body text — nav links, button labels, form fields, card copy, footer text, small caps labels. Inter handles the functional layer with neutral efficiency, letting the serif carry the personality. Weight 500 for nav and labels, 400 for body, 600 for emphasis.

- **Substitute:** Inter is freely available via Google Fonts; no substitute needed
- **Weights:** 400, 500, 600
- **Sizes:** 10px, 14px, 16px, 18px, 22px
- **Line height:** 1.20–1.50
- **Letter spacing:** -0.01em body, -0.02em small caps labels
- **OpenType features:** `"ss01" on, "cv11" on`
- **Portal 用法：** 侧栏、按钮、表格、表单、金额、辅助说明。**禁止**用 Inter 做 ≥22px 的页面主标题。

### Type Scale

| Role | Size | Line Height | Letter Spacing | Token |
|------|------|-------------|----------------|-------|
| caption | 10px | 1.2 | -0.2px | `--text-caption` |
| body-sm | 14px | 1.5 | -0.14px | `--text-body-sm` |
| body | 16px | 1.5 | -0.16px | `--text-body` |
| subheading | 18px | 1.5 | -0.18px | `--text-subheading` |
| heading-sm | 22px | 1.25 | -0.22px | `--text-heading-sm` |
| heading | 32px | 1.15 | -0.32px | `--text-heading` |
| heading-lg | 48px | 1.1 | -0.48px | `--text-heading-lg` |
| display | 64px | 1 | -0.64px | `--text-display` |

---

## 4. Tokens — Spacing & Shapes

**Base unit:** 8px  
**Density:** comfortable

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 8 | 8px | `--spacing-8` |
| 16 | 16px | `--spacing-16` |
| 24 | 24px | `--spacing-24` |
| 32 | 32px | `--spacing-32` |
| 48 | 48px | `--spacing-48` |
| 64 | 64px | `--spacing-64` |
| 96 | 96px | `--spacing-96` |

### Border Radius

| Element | Value |
|---------|-------|
| nav | 1440px |
| tags | 1440px |
| cards | 24px |
| icons | 1440px |
| images | 24-48px |
| buttons | 1440px |
| inputs | 1440px |

### Layout

- **Page max-width:** 1200px
- **Section gap:** 48-80px
- **Card padding:** 24-48px
- **Element gap:** 12-16px

---

## 5. Components（品牌原件）

### Primary CTA Button (Filled Yellow)

**Role:** Main action trigger — 'Get Started', 'Log In', 'Read More'

Background `#ffe228`, text `#130e30` in Inter 500 at 16px. Full pill radius 1440px. Padding 12px 24px. No shadow. Black text on yellow achieves 16.2:1 contrast. The yellow is so bright it functions as a highlighter; **one per viewport maximum**.

**Portal 映射：** 登录页「开发环境登录 / 使用飞书登录」、合同页「新建合同」、发票页「新建发票」、表单「保存」。同一屏只放一颗黄按钮。

### Secondary Button (Dark Pill)

**Role:** Alternative action — used for 'Log In' alongside primary CTA

Background `#130e30`, text `#ffffff` in Inter 500 at 16px. Full pill radius 1440px. Padding 12px 22px. Creates a dark/light button pair with the yellow primary for visual hierarchy.

**Portal 映射：** 和主操作并排的次要动作（例如「返回列表」）。删除用文字链，不用第二颗黄按钮。

### Email Input Field

**Role:** Hero email capture form

White background `#ffffff`, border 1px solid `#000000`, text `#130e30` in Inter 400 at 16px. Placeholder text in Slate `#5f5c6e`. Pill radius 1440px — the input and its adjacent button share the same radius creating a continuous capsule. Padding 12px 22px.

**Portal 映射：** 所有表单控件（文本、数字、日期、下拉、多行）都用这套描边和胶囊圆角。多行文本框圆角可降到 24px，避免椭圆气泡。

### Logo Lockup

**Role:** Brand identity in nav and footer

Mark + wordmark in `#130e30`. The mark uses a leaf/petal shape echoing the organic decorative blobs. Always paired with a nav layout, never standalone.

**Portal 映射：** 侧栏 / 登录卡左上：叶瓣形色块 + 词标 `Portal`。

### Nav Bar

**Role:** Top-level site navigation

Background `#eff2e5`, horizontal layout with logo left, nav links center (Inter 500 16px in `#130e30`), CTA pair right. No shadow, sits flush on canvas.

**Portal 映射：** 内部系统用 **左侧导航**，但表面仍是 Soft Meadow，链接是 Inter 500 / Deep Ink。当前项不用第二种彩色，用 Deep Ink 字重或浅描边即可。合同、发票在导航里是并列入口，不嵌套。

### Hero Card / Product Mockup Container

**Role:** Showcases the product UI with decorative blob backdrop

White product card sits on top of organic colored shapes (green, pink, yellow, violet). The card has subtle border-radius 24px. Behind it, SVG-style organic blobs in `#59e25d`, `#e261e5`, `#ffe228`, and `#130e30` create a garden-like atmosphere without illustration.

**Portal 映射：** 只在 **登录页** 背后放色块。登录后的工作台 / 合同 / 发票不再铺满色块，以免表格难读。

### Feature Card

**Role:** Content cards

Background `#eff2e5`, padding 24-48px, border-radius 24px. Hedvig Letters Serif heading at 22-32px in `#130e30`, body in Inter 16px `#5f5c6e`. No shadow or border — the surface contrast alone defines the card.

**Portal 映射：** 工作台统计卡、最近合同 / 最近发票列表卡、空状态卡。

### Small Caps Label

**Role:** Micro-copy above sections, case study tags, nav eyebrows

Inter 500 at 10-12px, letter-spacing -0.02em, color `#5f5c6e` or `#130e30`. All uppercase. Used sparingly as taxonomic labels rather than decoration.

**Portal 映射：** `DASHBOARD` / `CONTRACTS` / `INVOICES`、表格列头的辅助标签。

### Hero Headline

**Role:** Primary page title

Hedvig Letters Serif weight 700 at 48-64px, line-height 1.0-1.1, letter-spacing -0.01em, color `#130e30`.

**Portal 映射：** 登录页「欢迎回来」用 heading-lg；内部页标题用 heading（32px），不要每页都上 64px。

---

## 6. Portal 页面怎么落

合同和发票 **永远是两个模块**：

| | 合同 | 发票 |
| --- | --- | --- |
| 路由 | `/contracts` | `/invoices` |
| 接口 | `/api/v1/contracts` | `/api/v1/invoices` |
| 主 CTA | 本页唯一黄按钮「新建合同」 | 本页唯一黄按钮「新建发票」 |
| 关系 | 管合作关系 | 管开票；可选关联合同 |

不要做成「一个大表格里又有合同又有发票」。工作台只做入口，两列卡片分别链到两个模块。

内部页布局：

- 画布 `#f9fbf2`
- 侧栏 Soft Meadow，宽约 240–260px
- 主栏最大 1200px，左右留白
- 列表用 Soft Meadow 卡片包一层，表头 / 行用 Inter，金额可用等宽数字但字体仍是 Inter
- 不要给卡片或按钮加 drop shadow

---

## 7. Do's and Don'ts

### Do

- Use the 1440px pill radius on every button, input, nav link, tag, and icon container — the pill shape is the brand's signature geometry
- Pair the yellow CTA `#ffe228` with the dark pill `#130e30` for button hierarchy; never use two yellow buttons side by side
- Use Hedvig Letters Serif exclusively for headings ≥22px and Inter for everything below; never use Inter for headings or Hedvig for body copy
- Set body text to `#130e30` (not pure black) for warmth; reserve `#000000` for the logo mark, input borders, and high-contrast fine details
- Build the surface stack as Canvas `#f9fbf2` → Soft Meadow `#eff2e5` cards; the slight green tint is intentional and should be preserved
- Use the decorative organic blobs (green `#59e25d`, fuchsia `#e261e5`, yellow `#ffe228`, violet `#130e30`) only as background atmosphere behind hero/product visuals — never as UI fills or icon colors
- Tighten letter-spacing to -0.01em on all headings and -0.02em on small caps labels

### Don't

- Do not use sharp corners (<16px) on buttons, inputs, or nav items — the pill is non-negotiable
- Do not introduce additional accent colors into the UI; green, pink, and fuchsia are decoration-only and must not appear in buttons, badges, or status indicators
- Do not use pure white `#ffffff` for card surfaces when Soft Meadow `#eff2e5` is the designated card layer（输入框内部可以用白）
- Do not place two primary yellow CTAs in the same viewport; alternate with the dark pill for hierarchy
- Do not use Inter for display headlines or Hedvig Letters Serif for UI labels
- Do not add drop shadows to cards or buttons; surface differentiation comes from the green-tinted `#eff2e5` layer, not elevation
- Do not use Slate `#5f5c6e` for primary body text — it is reserved for muted copy and helper text only
- Do not 把合同和发票合成一个模块或一种「彩色编码」（上一版的薄荷 / 靛蓝双主色作废）

---

## 8. Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 0 | Canvas | `#f9fbf2` | Page background, outermost layer |
| 1 | Soft Meadow | `#eff2e5` | Card surface, nav bar, hero backdrop, elevated panels |
| 2 | Hi-Yellow Accent | `#ffe228` | Primary action surface — CTA buttons and highlight pills |
| 3 | Deep Ink | `#130e30` | Dark contrast surface — inverted chips, secondary buttons, not a full-page theme |

### Surface Temperature

The off-white tones are not neutral white — `#f9fbf2` has a faint warm-green cast and `#eff2e5` is a clearly green-tinted meadow surface. This warm canvas is core to the brand's organic, garden-influenced feel. Do not substitute pure `#ffffff` or neutral grays for page/card surfaces. The two surface tones create enough separation for cards without needing borders or shadows.

---

## 9. Imagery

Product UI screenshots are the primary visual asset — shown inside a white card floating above organic colored blob shapes in green, fuchsia, yellow, and violet. The blobs are flat, irregular, and overlapping, creating a garden-meadow feel. Iconography is minimal and line-style, not colorful. No 3D renders or illustrations of people — the visual identity is abstract, organic, and product-forward.

Portal 登录页可以放一组扁平不规则色块；登录后页面保持干净，让表格成为主角。

---

## 10. Layout（营销站参考 → 内部站取舍）

原规范：Max-width 1200px centered container. Hero is a two-column split. Sections alternate between canvas and Soft Meadow. Navigation is a simple top bar, not sticky. The layout breathes.

Portal 取舍：

- 保留 1200px 主栏、48px 级间距、24–48px 卡片内边距
- 导航改左侧，方便合同 / 发票继续加第三个模块
- 不做 Trustpilot、客户 Logo 墙、评价轮播——那些是营销站部件

---

## 11. Agent Prompt Guide

**Quick Color Reference**

- text (primary): `#130e30`
- text (muted): `#5f5c6e`
- background (page): `#f9fbf2`
- background (card): `#eff2e5`
- border: `#130e30` / `#000000` for inputs
- accent (decorative blobs only): `#ffe228`, `#59e25d`, `#e261e5`
- primary action: `#ffe228` (filled action)

**Example Component Prompts**

1. Create a Primary Action Button: `#ffe228` background, `#130e30` text, 1440px radius, compact pill padding. Use this filled treatment for the main CTA.
2. **Feature Grid Card**: Background `#eff2e5`, 24px border-radius, 32px padding. Heading in Hedvig Letters Serif 700 22px `#130e30`. Body in Inter 400 16px `#5f5c6e`.
3. **Top / Side Navigation**: Background `#eff2e5`. Links Inter 500 16px `#130e30`. If a CTA pair is needed: dark pill `#130e30` / white text + yellow filled `#ffe228` / `#130e30` text. Never two yellows.
4. **Form field**: White `#ffffff` fill, 1px `#000000` border, Inter 400 16px `#130e30`, placeholder `#5f5c6e`, pill radius 1440px, padding 12px 22px.

---

## 12. Similar Brands

- **Sweep (sweep.net)** — Same warm cream canvas, organic decorative blob shapes behind product UI, serif headline + sans body pairing, and pill-shaped yellow/dark CTA pair
- **Watershed (watershed.com)** — Sustainability/compliance domain with light surfaces, soft organic accents, and a single bright highlight color for CTAs
- **Klim (klim.co)** — CSR-adjacent SaaS with cream backgrounds, serif display type, pill buttons, and nature-inspired decorative elements
- **Notion** — Light off-white canvas, Inter for body type, pill-shaped buttons, and minimal card elevation

---

## 13. Quick Start — CSS Custom Properties

实现时把下面变量写进 `apps/web/src/app/globals.css`。Tailwind v4 用 `@theme` 暴露同名 token，页面里用 `bg-canvas`、`text-deep-ink`、`font-hedvig` 这类类名，不要再写死上一版的薄荷 / 靛蓝。

```css
:root {
  /* Colors */
  --color-deep-ink: #130e30;
  --color-hi-yellow: #ffe228;
  --color-moss-green: #59e25d;
  --color-fuchsia: #e261e5;
  --color-slate: #5f5c6e;
  --color-canvas: #f9fbf2;
  --color-soft-meadow: #eff2e5;
  --color-charcoal: #222222;
  --color-onyx: #000000;

  /* Typography — Font Families */
  --font-hedvig-letters-serif: "Hedvig Letters Serif", ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
  --font-inter: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

  /* Typography — Scale */
  --text-caption: 10px;
  --leading-caption: 1.2;
  --tracking-caption: -0.2px;
  --text-body-sm: 14px;
  --leading-body-sm: 1.5;
  --tracking-body-sm: -0.14px;
  --text-body: 16px;
  --leading-body: 1.5;
  --tracking-body: -0.16px;
  --text-subheading: 18px;
  --leading-subheading: 1.5;
  --tracking-subheading: -0.18px;
  --text-heading-sm: 22px;
  --leading-heading-sm: 1.25;
  --tracking-heading-sm: -0.22px;
  --text-heading: 32px;
  --leading-heading: 1.15;
  --tracking-heading: -0.32px;
  --text-heading-lg: 48px;
  --leading-heading-lg: 1.1;
  --tracking-heading-lg: -0.48px;
  --text-display: 64px;
  --leading-display: 1;
  --tracking-display: -0.64px;

  /* Typography — Weights */
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Spacing */
  --spacing-unit: 8px;
  --spacing-8: 8px;
  --spacing-16: 16px;
  --spacing-24: 24px;
  --spacing-32: 32px;
  --spacing-48: 48px;
  --spacing-64: 64px;
  --spacing-96: 96px;

  /* Layout */
  --page-max-width: 1200px;
  --section-gap: 64px;
  --card-padding: 32px;
  --element-gap: 16px;

  /* Border Radius */
  --radius-3xl: 24px;
  --radius-full: 48px;
  --radius-full-2: 1440px;

  /* Named Radii */
  --radius-nav: 1440px;
  --radius-tags: 1440px;
  --radius-cards: 24px;
  --radius-icons: 1440px;
  --radius-images: 32px;
  --radius-buttons: 1440px;

  /* Surfaces */
  --surface-canvas: #f9fbf2;
  --surface-soft-meadow: #eff2e5;
  --surface-hi-yellow-accent: #ffe228;
  --surface-deep-ink: #130e30;
}
```

### Tailwind v4 `@theme`

```css
@theme {
  --color-deep-ink: #130e30;
  --color-hi-yellow: #ffe228;
  --color-moss-green: #59e25d;
  --color-fuchsia: #e261e5;
  --color-slate: #5f5c6e;
  --color-canvas: #f9fbf2;
  --color-soft-meadow: #eff2e5;
  --color-charcoal: #222222;
  --color-onyx: #000000;

  --font-hedvig-letters-serif: "Hedvig Letters Serif", ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
  --font-inter: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

  --text-caption: 10px;
  --leading-caption: 1.2;
  --tracking-caption: -0.2px;
  --text-body-sm: 14px;
  --leading-body-sm: 1.5;
  --tracking-body-sm: -0.14px;
  --text-body: 16px;
  --leading-body: 1.5;
  --tracking-body: -0.16px;
  --text-subheading: 18px;
  --leading-subheading: 1.5;
  --tracking-subheading: -0.18px;
  --text-heading-sm: 22px;
  --leading-heading-sm: 1.25;
  --tracking-heading-sm: -0.22px;
  --text-heading: 32px;
  --leading-heading: 1.15;
  --tracking-heading: -0.32px;
  --text-heading-lg: 48px;
  --leading-heading-lg: 1.1;
  --tracking-heading-lg: -0.48px;
  --text-display: 64px;
  --leading-display: 1;
  --tracking-display: -0.64px;

  --spacing-8: 8px;
  --spacing-16: 16px;
  --spacing-24: 24px;
  --spacing-32: 32px;
  --spacing-48: 48px;
  --spacing-64: 64px;
  --spacing-96: 96px;

  --radius-3xl: 24px;
  --radius-full: 48px;
  --radius-full-2: 1440px;
}
```

---

## 14. 落地顺序（给下一次改代码用）

1. 把第 13 节变量写进 `globals.css`，用 `next/font` 接入 **Hedvig Letters Serif** 与 **Inter**。
2. 重写登录页：Canvas + 背后色块 + Soft Meadow 卡片 + 一颗黄 CTA。
3. 侧栏、工作台、合同、发票共用 token；合同 / 发票页面文件保持分开。
4. 去掉上一版深色网格、薄荷绿、靛蓝双主色。
5. 对照第 7 节 Do / Don't 扫一遍：一屏是否只有一颗黄按钮、卡片是否无阴影、绿粉是否只出现在装饰色块。
