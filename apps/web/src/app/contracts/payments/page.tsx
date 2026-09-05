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
      <PageHeader
        eyebrow="Contracts"
        title="回款"
        description="合同房间里的到账流水。点合同名称可以回到那份合同继续登记。"
      />

      <section className="mb-8 grid gap-6 sm:grid-cols-2">
        <div className="ui-card p-6">
          <p className="eyebrow">回款笔数</p>
          <p className="stat-value mt-3">{rows.length}</p>
        </div>
        <div className="ui-card p-6">
          <p className="eyebrow">回款合计</p>
          <p className="stat-value mt-3">{money(total)}</p>
        </div>
      </section>

      <div className="ui-card overflow-x-auto">
        <table className="ui-table">
          <thead>
            <tr>
              <th>到账日</th>
              <th>合同</th>
              <th>甲 / 乙</th>
              <th>期次</th>
              <th>金额</th>
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
                <tr key={row.id}>
                  <td>{row.received_at || "—"}</td>
                  <td>
                    <Link href={`/contracts/${row.contract_id}?tab=payments`} className="font-medium hover:underline">
                      {row.contract_title}
                    </Link>
                    <p className="mt-1 text-[12px] text-mid-gray">{row.contract_no || `未编号 · ID ${row.contract_id}`}</p>
                  </td>
                  <td>
                    {row.party_a || "—"} / {row.party_b || "—"}
                  </td>
                  <td>{row.schedule_name || "—"}</td>
                  <td>{money(row.amount)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
