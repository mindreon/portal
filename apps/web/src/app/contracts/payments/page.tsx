"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { EmptyHint, PageHeader } from "@/components/ui";
import { api, money } from "@/lib/api";
import type { CollectionRow } from "@/lib/types";

export default function ContractPaymentsPage() {
  const [rows, setRows] = useState<CollectionRow[]>([]);

  useEffect(() => {
    api<CollectionRow[]>("/api/v1/contracts/payments").then(setRows);
  }, []);

  const total = rows.reduce((sum, item) => sum + Number(item.amount), 0);

  return (
    <AppShell>
      <PageHeader eyebrow="Contracts" title="回款" />
      <p className="-mt-3 mb-5 text-body text-mid-gray">
        合同房间里的到账流水。点合同名称可以回到那份合同继续登记。
      </p>

      <section className="mb-8 grid gap-2 sm:grid-cols-2">
        <div className="ui-card p-5">
          <p className="eyebrow">回款笔数</p>
          <p className="stat-value mt-2">{rows.length}</p>
        </div>
        <div className="ui-card p-5">
          <p className="eyebrow">回款合计</p>
          <p className="stat-value mt-2">{money(total)}</p>
        </div>
      </section>

      <div className="ui-card overflow-hidden">
        <table className="w-full text-left text-body">
          <thead className="text-mid-gray">
            <tr>
              <th className="px-5 py-3 font-medium">到账日</th>
              <th className="px-5 py-3 font-medium">合同</th>
              <th className="px-5 py-3 font-medium">甲 / 乙</th>
              <th className="px-5 py-3 font-medium">期次</th>
              <th className="px-5 py-3 font-medium">金额</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5}>
                  <EmptyHint>还没有回款。打开某份合同，在「回款」页签登记到账。</EmptyHint>
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-t border-hairline">
                  <td className="px-5 py-3">{row.received_at || "—"}</td>
                  <td className="px-5 py-3">
                    <Link href={`/contracts/${row.contract_id}?tab=payments`} className="font-medium hover:underline">
                      {row.contract_title}
                    </Link>
                    <p className="text-[12px] text-mid-gray">{row.contract_no || `未编号 · ID ${row.contract_id}`}</p>
                  </td>
                  <td className="px-5 py-3">
                    {row.party_a || "—"} / {row.party_b || "—"}
                  </td>
                  <td className="px-5 py-3">{row.schedule_name || "—"}</td>
                  <td className="px-5 py-3">{money(row.amount)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
