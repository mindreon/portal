import Link from "next/link";

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        <h2 className="heading">{title}</h2>
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

/** 列表默认一页几条。前端只请求这一页，搜索和下拉也走同一个分页接口。 */
export const PAGE_SIZE = 10;

export function Pager({
  page,
  total,
  pageSize = PAGE_SIZE,
  onPage,
}: {
  page: number;
  total: number;
  pageSize?: number;
  onPage: (next: number) => void;
}) {
  if (total <= 0) return null;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
      <p className="text-body text-mid-gray">
        共 {total} 条 · 每页 {pageSize} 条 · 第 {page} / {pages} 页
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="ui-btn ui-btn-secondary"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          上一页
        </button>
        <button
          type="button"
          className="ui-btn ui-btn-secondary"
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  );
}

/** 甲方、乙方各占一行。前面标甲/乙，扫一眼就能对上。 */
export function PartyStack({ a, b }: { a?: string | null; b?: string | null }) {
  return (
    <div className="ui-party-stack">
      <p>
        <span className="text-mid-gray">甲 </span>
        {a?.trim() || "—"}
      </p>
      <p>
        <span className="text-mid-gray">乙 </span>
        {b?.trim() || "—"}
      </p>
    </div>
  );
}
