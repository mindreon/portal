import { redirect } from "next/navigation";

/** 旧「回款 / 收付款」入口，转到账单页。 */
export default function PaymentsRedirectPage() {
  redirect("/contracts/bills");
}
