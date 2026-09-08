"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PinnedTable } from "@/components/pinned-table";
import { StatusBadge } from "@/components/status-badge";
import { EmptyHint, PAGE_SIZE, PageHeader, Pager, PartyStack } from "@/components/ui";
import { api, money, withQuery } from "@/lib/api";
import { useImportLive } from "@/lib/live";
import type { Contract, ContractSummary, PageResult } from "@/lib/types";

function isParsing(status: string) {
  return status === "pending" || status === "processing";
}

function fileLabel(row: Contract) {
  if (row.source_filename) {
    return row.source_filename.split("/").pop() || row.source_filename;
  }
  return row.title;
}

export default function ContractsPage() {
  const [rows, setRows] = useState<Contract[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ContractSummary | null>(null);
  const [party, setParty] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [filters, setFilters] = useState({ party: "", dateFrom: "", dateTo: "" });
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const [list, nextSummary] = await Promise.all([
        api<PageResult<Contract>>(
          withQuery("/api/v1/contracts", {
            party: filters.party,
            date_from: filters.dateFrom,
            date_to: filters.dateTo,
            page,
            page_size: PAGE_SIZE,
          }),
        ),
        api<ContractSummary>("/api/v1/contracts/summary"),
      ]);
      if (cancelled) return;
      setRows(list.items);
      setTotal(list.total);
      setSummary(nextSummary);
      if (list.total > 0 && list.items.length === 0 && page > 1) {
        setPage(list.page > 1 ? list.page - 1 : 1);
      }
    }
    load().catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [filters, page]);

  const parsing = (summary?.parsing_count ?? 0) > 0 || rows.some((row) => isParsing(row.parse_status));

  useImportLive(parsing, () => {
    setFilters((current) => ({ ...current }));
  });

  function onFilter(event: React.FormEvent) {
    event.preventDefault();
    setPage(1);
    setFilters({ party: party.trim(), dateFrom, dateTo });
  }

  return (
    <AppShell>
      <PageHeader
        title="合同"
        action={
          <Link href="/contracts/new" className="ui-btn ui-btn-primary">
            新建合同
          </Link>
        }
      />

      <section className="mb-8 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatBlock label="合同总数" value={String(summary?.count ?? 0)} />
        <StatBlock label="履约中" value={String(summary?.active_count ?? 0)} />
        <StatBlock label="合同总额" value={money(summary?.total_amount ?? 0)} />
        <StatBlock label="待回款" value={money(summary?.outstanding_amount ?? 0)} />
      </section>

      {parsing ? (
        <p className="mb-6 text-body text-mid-gray">有合同正在后台识别，完成后会自动更新。离开或刷新页面不会中断。</p>
      ) : null}

      <form onSubmit={onFilter} className="ui-card mb-6 flex flex-wrap items-end gap-4 p-6">
        <label className="min-w-[200px] flex-1 text-body">
          <span className="mb-2 block font-medium text-ink">合同双方 / 文件名</span>
          <input
            value={party}
            onChange={(event) => setParty(event.target.value)}
            placeholder="模糊匹配甲方、乙方或文件名"
            className="ui-input"
          />
        </label>
        <label className="text-body">
          <span className="mb-2 block font-medium text-ink">开始日期</span>
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} className="ui-input" />
        </label>
        <label className="text-body">
          <span className="mb-2 block font-medium text-ink">结束日期</span>
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} className="ui-input" />
        </label>
        <div className="flex flex-wrap gap-3">
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
              setPage(1);
              setFilters({ party: "", dateFrom: "", dateTo: "" });
            }}
          >
            重置
          </button>
        </div>
      </form>

      <PinnedTable pinLeft={1} pinRight={1} minWidth={1280}>
        <thead>
          <tr>
            <th>文件名</th>
            <th>合同</th>
            <th>甲乙</th>
            <th className="ui-money">金额</th>
            <th className="ui-money">已回款</th>
            <th>状态</th>
            <th className="ui-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={7}>
                <EmptyHint>没有匹配的合同。可以点右上角新建，或放宽筛选。</EmptyHint>
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <Link href={`/contracts/${row.id}`} className="font-medium hover:underline">
                    {fileLabel(row)}
                  </Link>
                  {row.source_filename && row.source_filename.includes("/") ? (
                    <p className="mt-1 text-[12px] text-mid-gray">{row.source_filename}</p>
                  ) : null}
                </td>
                <td>
                  <p className="font-medium text-ink">{row.title}</p>
                  <p className="mt-1 text-[12px] text-mid-gray">
                    {row.contract_no || `未编号 · ID ${row.id}`}
                    {row.subject_name ? ` · ${row.subject_name}` : ""}
                  </p>
                </td>
                <td>
                  <PartyStack a={row.party_a} b={row.party_b || row.counterparty} />
                </td>
                <td className="ui-money">{money(row.amount, row.currency)}</td>
                <td className="ui-money">{money(row.collected_amount, row.currency)}</td>
                <td>
                  {isParsing(row.parse_status) || row.parse_status === "failed" ? (
                    <StatusBadge kind="parse" value={row.parse_status} />
                  ) : (
                    <StatusBadge kind="contract" value={row.status} />
                  )}
                </td>
                <td className="ui-actions">
                  <div className="ui-actions-row">
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
      </PinnedTable>
      <Pager page={page} total={total} onPage={setPage} />
    </AppShell>
  );
}

function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="ui-card min-w-0 p-6">
      <p className="eyebrow">{label}</p>
      <p className="stat-value mt-3">{value}</p>
    </div>
  );
}
