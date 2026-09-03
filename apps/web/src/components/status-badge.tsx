import { CONTRACT_STATUS_LABEL, INVOICE_STATUS_LABEL } from "@/lib/types";

const TONES: Record<string, string> = {
  draft: "bg-[#efe6d6] text-[#6b4f2a]",
  active: "bg-[#dcecdf] text-[#215c38]",
  issued: "bg-[#dcecdf] text-[#215c38]",
  paid: "bg-[#d7e6f4] text-[#1d4f74]",
  expired: "bg-[#f3e2c7] text-[#8a4b12]",
  terminated: "bg-[#eadfdf] text-[#7a3030]",
  void: "bg-[#eadfdf] text-[#7a3030]",
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
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs ${TONES[value] ?? "bg-stone-200"}`}>
      {label}
    </span>
  );
}
