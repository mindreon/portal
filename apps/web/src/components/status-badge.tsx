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
