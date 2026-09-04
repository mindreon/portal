"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { EmptyHint, PageHeader } from "@/components/ui";
import { api, money } from "@/lib/api";
import type { Contract, ContractSummary } from "@/lib/types";

export default function ContractsPage() {
  const [rows, setRows] = useState<Contract[]>([]);
  const [summary, setSummary] = useState<ContractSummary | null>(null);
  const [party, setParty] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  async function load(nextParty = party, nextFrom = dateFrom, nextTo = dateTo) {
    const params = new URLSearchParams();
    if (nextParty.trim()) params.set("party", nextParty.trim());
    if (nextFrom) params.set("date_from", nextFrom);
    if (nextTo) params.set("date_to", nextTo);
    const query = params.toString();
    const [list, nextSummary] = await Promise.all([
      api<Contract[]>(`/api/v1/contracts${query ? `?${query}` : ""}`),
      api<ContractSummary>("/api/v1/contracts/summary"),
    ]);
    setRows(list);
    setSummary(nextSummary);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  function onFilter(event: React.FormEvent) {
    event.preventDefault();
    load().catch(() => undefined);
  }

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

      <section className="mb-8 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <StatBlock label="合同总数" value={String(summary?.count ?? 0)} />
        <StatBlock label="履约中" value={String(summary?.active_count ?? 0)} />
        <StatBlock label="合同总额" value={money(summary?.total_amount ?? 0)} />
        <StatBlock label="待回款" value={money(summary?.outstanding_amount ?? 0)} />
      </section>

      <form onSubmit={onFilter} className="ui-card mb-3 flex flex-wrap items-end gap-3 p-5">
        <label className="min-w-[200px] flex-1 text-body">
          <span className="mb-1.5 block font-medium text-ink">合同双方</span>
          <input
            value={party}
            onChange={(event) => setParty(event.target.value)}
            placeholder="模糊匹配甲方或乙方"
            className="ui-input"
          />
        </label>
        <label className="text-body">
          <span className="mb-1.5 block font-medium text-ink">开始日期</span>
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} className="ui-input" />
        </label>
        <label className="text-body">
          <span className="mb-1.5 block font-medium text-ink">结束日期</span>
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} className="ui-input" />
        </label>
        <button type="submit" className="ui-btn ui-btn-primary">
          筛选
        </button>
        <button
          type="button"
          className="ui-btn ui-btn-secondary"
          onClick={() => {
            setParty("");
            setDateFrom("");
            setDateTo("");
            load("", "", "").catch(() => undefined);
          }}
        >
          重置
        </button>
      </form>

      <div className="ui-card overflow-hidden">
        <table className="w-full text-left text-body">
          <thead className="text-mid-gray">
            <tr>
              <th className="px-5 py-3 font-medium">合同</th>
              <th className="px-5 py-3 font-medium">甲 / 乙</th>
              <th className="px-5 py-3 font-medium">金额</th>
              <th className="px-5 py-3 font-medium">已回款</th>
              <th className="px-5 py-3 font-medium">状态</th>
              <th className="px-5 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <EmptyHint>没有匹配的合同。可以点右上角新建，或放宽筛选。</EmptyHint>
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-t border-hairline">
                  <td className="px-5 py-3">
                    <Link href={`/contracts/${row.id}`} className="font-medium hover:underline">
                      {row.title}
                    </Link>
                    <p className="text-[12px] text-mid-gray">{row.contract_no || `未编号 · ID ${row.id}`}</p>
                  </td>
                  <td className="px-5 py-3">
                    {row.party_a || "—"} / {row.party_b || row.counterparty || "—"}
                  </td>
                  <td className="px-5 py-3">{money(row.amount, row.currency)}</td>
                  <td className="px-5 py-3">{money(row.collected_amount, row.currency)}</td>
                  <td className="px-5 py-3">
                    <StatusBadge kind="contract" value={row.status} />
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex flex-wrap gap-3">
                      <Link href={`/contracts/${row.id}`} className="font-medium underline-offset-4 hover:underline">
                        查看
                      </Link>
                      <Link
                        href={`/contracts/${row.id}?tab=payments`}
                        className="font-medium underline-offset-4 hover:underline"
                      >
                        回款
                      </Link>
                    </div>
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

function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="ui-card p-5">
      <p className="eyebrow">{label}</p>
      <p className="stat-value mt-2">{value}</p>
    </div>
  );
}
