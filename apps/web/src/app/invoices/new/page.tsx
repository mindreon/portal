import { InvoiceEditor } from "../invoice-editor";

export default async function NewInvoicePage({
  searchParams,
}: {
  searchParams: Promise<{ contract?: string }>;
}) {
  const query = await searchParams;
  return <InvoiceEditor defaultContractId={query.contract} />;
}
