# Shared UI primitives

Source directory: `apps/web/src/components/`. No shadcn/ui. Primitives are custom CSS classes in `globals.css` plus a few React helpers.

## PageHeader — `apps/web/src/components/ui.tsx`

Page title block: uppercase English eyebrow + Chinese heading + optional description + optional right-side action.

```tsx
import Link from "next/link";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="heading mt-2">{title}</h2>
        {description ? <p className="mt-3 text-body text-mid-gray">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-body text-mid-gray">
      <span className="mb-2 block font-medium text-ink">{label}</span>
      {children}
    </label>
  );
}

export function FormError({ message }: { message: string }) {
  if (!message) return null;
  return <p className="rounded-[18px] bg-canvas px-4 py-3 text-body text-ember">{message}</p>;
}

export function EmptyHint({ children }: { children: React.ReactNode }) {
  return <p className="px-6 py-14 text-center text-body text-mid-gray">{children}</p>;
}

export function TextLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="text-body font-medium text-ink underline-offset-4 hover:underline">
      {children}
    </Link>
  );
}
```

Buttons, inputs, cards are CSS classes (`.ui-btn`, `.ui-input`, `.ui-card`), not React components.

## StatusBadge — `apps/web/src/components/status-badge.tsx`

Monochrome status pills. Active/issued/processing = dark fill; draft/expired = canvas gray.

```tsx
import { CONTRACT_STATUS_LABEL, INVOICE_STATUS_LABEL, PARSE_STATUS_LABEL } from "@/lib/types";

const TONES: Record<string, string> = {
  draft: "bg-canvas text-ink-soft",
  active: "bg-ink-soft text-[#fafafa]",
  issued: "bg-ink-soft text-[#fafafa]",
  paid: "bg-ink text-[#fafafa]",
  expired: "bg-canvas text-mid-gray",
  terminated: "bg-canvas text-mid-gray",
  void: "bg-canvas text-mid-gray",
  pending: "bg-canvas text-ink-soft",
  processing: "bg-ink-soft text-[#fafafa]",
  done: "bg-canvas text-ink-soft",
  failed: "bg-canvas text-mid-gray",
};

const LABELS: Record<"contract" | "invoice" | "parse", Record<string, string>> = {
  contract: CONTRACT_STATUS_LABEL,
  invoice: INVOICE_STATUS_LABEL,
  parse: PARSE_STATUS_LABEL,
};

export function StatusBadge({
  value,
  kind,
}: {
  value: string;
  kind: "contract" | "invoice" | "parse";
}) {
  const label = LABELS[kind][value] ?? value;
  return (
    <span
      className={`inline-block rounded-[18px] px-2.5 py-1 text-[12px] font-medium ${TONES[value] ?? "bg-canvas text-ink-soft"}`}
    >
      {label}
    </span>
  );
}
```

## LogoMark / LogoLockup — `apps/web/src/components/logo.tsx`

Black rounded square with a white geometric “P” path. Lockup: 28px mark + uppercase “Internal” eyebrow + “Portal”.

```tsx
export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" aria-hidden="true">
      <rect width="28" height="28" rx="8" fill="#0a0a0a" />
      <path d="M8 18.5V9.5h4.2c2.4 0 3.8 1.3 3.8 3.3 0 2.1-1.5 3.4-3.9 3.4H10.4V18.5H8Zm2.4-4.2h1.6c1.1 0 1.7-.5 1.7-1.4s-.6-1.4-1.7-1.4H10.4v2.8Z" fill="#fafafa" />
    </svg>
  );
}

export function LogoLockup() {
  return (
    <div className="flex items-center gap-3">
      <LogoMark />
      <div>
        <p className="eyebrow">Internal</p>
        <p className="text-[16px] font-semibold tracking-[-0.4px] text-ink">Portal</p>
      </div>
    </div>
  );
}
```

## Breadcrumbs — `apps/web/src/components/breadcrumbs.tsx`

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { crumbsFor } from "@/lib/modules";

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true" className="text-mid-gray">
      <path d="M4.2 2.4 7.8 6 4.2 9.6" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const crumbs = crumbsFor(pathname);

  return (
    <nav aria-label="面包屑" className="flex flex-wrap items-center gap-2 text-body">
      {crumbs.map((crumb, index) => {
        const last = index === crumbs.length - 1;
        return (
          <span key={`${crumb.label}-${index}`} className="flex items-center gap-2">
            {index > 0 ? <Chevron /> : null}
            {crumb.href && !last ? (
              <Link href={crumb.href} className="text-mid-gray hover:text-ink">
                {crumb.label}
              </Link>
            ) : (
              <span className="text-ink">{crumb.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
```

## PinnedTable — `apps/web/src/components/pinned-table.tsx`

White card wrapping a table. Sticky left/right columns. See full file in repo; visual: `.ui-card.ui-pinned-table` + `.ui-table`.

## SearchPalette — `apps/web/src/components/search-palette.tsx`

Header search trigger: gray capsule, placeholder “搜索模块或记录…”, right `⌘K` kbd. Overlay command palette with gray input and two-line hits (title + uppercase meta). Full source in repo.
