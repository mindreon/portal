import { CONTRACT_STATUS_LABEL, INVOICE_STATUS_LABEL } from "@/lib/types";

const TONES: Record<string, string> = {
  draft: "bg-white/10 text-[var(--muted)]",
  active: "bg-[var(--mint)]/15 text-[var(--mint)]",
  issued: "bg-[var(--indigo)]/20 text-[#c4b8ff]",
  paid: "bg-[var(--mint)]/15 text-[var(--mint)]",
  expired: "bg-amber-400/15 text-amber-200",
  terminated: "bg-[var(--danger)]/12 text-[var(--danger)]",
  void: "bg-[var(--danger)]/12 text-[var(--danger)]",
};

export function StatusBadge({
  value,
  kind,
}: {
  value: string;
  kind: "contract" | "invoice";
}) {
  const label = (kind === "contract" ? CONTRACT_STATUS_LABEL : INVOICE_STATUS_LABEL)[value] ?? value;
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${TONES[value] ?? "bg-white/10"}`}>
      {label}
    </span>
  );
}
