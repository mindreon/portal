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
          <Link href="/contracts/new" className="ui-btn ui-btn-mint">
            新建合同
          </Link>
        }
      />
      <p className="-mt-4 mb-6 text-sm text-[var(--muted)]">
        这是独立模块。先把合作关系立住；发票在隔壁模块，需要时再挂过来。
      </p>

      <div className="ui-card overflow-hidden rounded-3xl">
        <table className="w-full text-left text-sm">
          <thead className="bg-white/5 text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3 font-medium">合同</th>
              <th className="px-4 py-3 font-medium">对方</th>
              <th className="px-4 py-3 font-medium">金额</th>
              <th className="px-4 py-3 font-medium">状态</th>
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
                <tr key={row.id} className="border-t border-[var(--line)]">
                  <td className="px-4 py-3">
                    <Link href={`/contracts/${row.id}`} className="font-medium hover:text-[var(--mint)]">
                      {row.title}
                    </Link>
                    <p className="font-mono-num text-xs text-[var(--muted)]">{row.contract_no}</p>
                  </td>
                  <td className="px-4 py-3">{row.counterparty}</td>
                  <td className="font-mono-num px-4 py-3">{money(row.amount, row.currency)}</td>
                  <td className="px-4 py-3">
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
