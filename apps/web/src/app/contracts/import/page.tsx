import { redirect } from "next/navigation";

export default function ContractImportRedirectPage() {
  redirect("/contracts/new");
}
