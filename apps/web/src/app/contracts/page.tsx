"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { EmptyHint, PageHeader } from "@/components/ui";
import { api, money } from "@/lib/api";
import type { Contract } from "@/lib/types";

export default function ContractsPage() {
  const [rows, setRows] = useState<Contract[]>([]);

  useEffect(() => {
    api<Contract[]>("/api/v1/contracts").then(setRows);
  }, []);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Contracts"
        title="合同"
        action={
          <Link href="/contracts/new" className="ui-btn ui-btn-primary">
            新建合同
          </Link>
        }
      />
      <p className="-mt-3 mb-5 text-body text-mid-gray">
        独立模块。先把合作关系立住；发票在隔壁模块，需要时再挂过来。
      </p>

      <div className="ui-card overflow-hidden">
        <table className="w-full text-left text-body">
          <thead className="text-mid-gray">
            <tr>
              <th className="px-5 py-3 font-medium">合同</th>
              <th className="px-5 py-3 font-medium">对方</th>
              <th className="px-5 py-3 font-medium">金额</th>
              <th className="px-5 py-3 font-medium">状态</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4}>
                  <EmptyHint>还没有合同。点右上角新建第一条。</EmptyHint>
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-t border-hairline">
                  <td className="px-5 py-3">
                    <Link href={`/contracts/${row.id}`} className="font-medium hover:underline">
                      {row.title}
                    </Link>
                    <p className="text-[12px] text-mid-gray">{row.contract_no}</p>
                  </td>
                  <td className="px-5 py-3">{row.counterparty}</td>
                  <td className="px-5 py-3">{money(row.amount, row.currency)}</td>
                  <td className="px-5 py-3">
                    <StatusBadge kind="contract" value={row.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
