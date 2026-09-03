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
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="heading mt-1">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-body text-mid-gray">
      <span className="mb-1.5 block font-medium text-ink">{label}</span>
      {children}
    </label>
  );
}

export function FormError({ message }: { message: string }) {
  if (!message) return null;
  return <p className="rounded-[18px] bg-canvas px-3 py-2 text-body text-ember">{message}</p>;
}

export function EmptyHint({ children }: { children: React.ReactNode }) {
  return <p className="px-5 py-10 text-center text-body text-mid-gray">{children}</p>;
}

export function TextLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="text-body font-medium text-ink underline-offset-4 hover:underline">
      {children}
    </Link>
  );
}
