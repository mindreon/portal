import { CONTRACT_STATUS_LABEL, INVOICE_STATUS_LABEL } from "@/lib/types";

const TONES: Record<string, string> = {
  draft: "bg-canvas text-ink-soft",
  active: "bg-ink-soft text-[#fafafa]",
  issued: "bg-ink-soft text-[#fafafa]",
  paid: "bg-ink text-[#fafafa]",
  expired: "bg-canvas text-mid-gray",
  terminated: "bg-canvas text-mid-gray",
  void: "bg-canvas text-mid-gray",
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
      className={`inline-block rounded-[18px] px-2 py-[2px] text-[12px] font-medium ${TONES[value] ?? "bg-canvas text-ink-soft"}`}
    >
      {label}
    </span>
  );
}
