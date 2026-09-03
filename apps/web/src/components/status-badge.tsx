import { CONTRACT_STATUS_LABEL, INVOICE_STATUS_LABEL } from "@/lib/types";

const TONES: Record<string, string> = {
  draft: "bg-canvas text-slate",
  active: "bg-hi-yellow text-deep-ink",
  issued: "bg-hi-yellow text-deep-ink",
  paid: "bg-deep-ink text-white",
  expired: "bg-canvas text-slate",
  terminated: "bg-canvas text-slate",
  void: "bg-canvas text-slate",
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
    <span
      className={`inline-block rounded-[1440px] px-3 py-1 text-[10px] font-medium uppercase tracking-[-0.02em] ${TONES[value] ?? "bg-canvas text-slate"}`}
    >
      {label}
    </span>
  );
}
