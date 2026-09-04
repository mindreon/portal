import { ContractWorkspace } from "../contract-workspace";

const TABS = ["fields", "files", "invoices", "payments"] as const;

export default async function EditContractPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ tab?: string }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const tab = TABS.includes(query.tab as (typeof TABS)[number]) ? (query.tab as (typeof TABS)[number]) : "fields";
  return <ContractWorkspace contractId={Number(id)} initialTab={tab} />;
}
