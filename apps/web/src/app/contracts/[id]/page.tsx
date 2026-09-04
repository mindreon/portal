import { ContractWorkspace } from "../contract-workspace";

export default async function EditContractPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ContractWorkspace contractId={Number(id)} />;
}
