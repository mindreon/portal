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

/** 甲方、乙方各占一行，长公司名不会把后面的金额挤换行。 */
export function PartyStack({ a, b }: { a?: string | null; b?: string | null }) {
  return (
    <div>
      <p>{a?.trim() || "—"}</p>
      <p className="mt-1">{b?.trim() || "—"}</p>
    </div>
  );
}
