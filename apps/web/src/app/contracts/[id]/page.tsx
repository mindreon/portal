import { ContractEditor } from "../contract-editor";

export default async function EditContractPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ContractEditor contractId={Number(id)} />;
}
