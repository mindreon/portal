import Link from "next/link";

export function PageHeader({
  eyebrow,
  title,
  action,
}: {
  eyebrow: string;
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="heading mt-2">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-body-sm text-slate">
      <span className="mb-2 block font-medium text-deep-ink">{label}</span>
      {children}
    </label>
  );
}

export function FormError({ message }: { message: string }) {
  if (!message) return null;
  return (
    <p className="rounded-[24px] bg-soft-meadow px-4 py-3 text-body-sm text-deep-ink">
      {message}
    </p>
  );
}

export function EmptyHint({ children }: { children: React.ReactNode }) {
  return <p className="px-4 py-10 text-center text-body-sm text-slate">{children}</p>;
}

export function TextLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="text-body-sm font-medium text-deep-ink underline-offset-4 hover:underline">
      {children}
    </Link>
  );
}
