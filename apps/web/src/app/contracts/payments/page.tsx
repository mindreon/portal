"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PinnedTable } from "@/components/pinned-table";
import { EmptyHint, PAGE_SIZE, PageHeader, Pager, PartyStack } from "@/components/ui";
import { api, money, withQuery } from "@/lib/api";
import type { CollectionPage, CollectionRow } from "@/lib/types";

export default function ContractPaymentsPage() {
  const [rows, setRows] = useState<CollectionRow[]>([]);
  const [total, setTotal] = useState(0);
  const [totalAmount, setTotalAmount] = useState("0");
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    api<CollectionPage>(withQuery("/api/v1/contracts/payments", { q: appliedQuery, page, page_size: PAGE_SIZE }))
      .then((list) => {
        if (cancelled) return;
        setRows(list.items);
        setTotal(list.total);
        setTotalAmount(list.total_amount);
        if (list.total > 0 && list.items.length === 0 && page > 1) {
          setPage(list.page > 1 ? list.page - 1 : 1);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [appliedQuery, page]);

  function onSearch(event: React.FormEvent) {
    event.preventDefault();
    setPage(1);
    setAppliedQuery(query.trim());
  }

  return (
    <AppShell>
      <PageHeader
        title="回款"
        description="合同房间里的到账流水。点合同名称可以回到那份合同继续登记。"
      />

      <section className="mb-8 grid gap-6 sm:grid-cols-2">
        <div className="ui-card p-6">
          <p className="eyebrow">回款笔数</p>
          <p className="stat-value mt-3">{total}</p>
        </div>
        <div className="ui-card p-6">
          <p className="eyebrow">回款合计</p>
          <p className="stat-value mt-3">{money(totalAmount)}</p>
        </div>
      </section>

      <form onSubmit={onSearch} className="ui-card mb-6 flex flex-wrap items-end gap-4 p-6">
        <label className="min-w-[200px] flex-1 text-body">
          <span className="mb-2 block font-medium text-ink">搜索</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="合同名称、编号或甲乙方"
            className="ui-input"
          />
        </label>
        <div className="flex flex-wrap gap-3">
          <button type="submit" className="ui-btn ui-btn-primary">
            搜索
          </button>
          <button
            type="button"
            className="ui-btn ui-btn-secondary"
            onClick={() => {
              setQuery("");
              setPage(1);
              setAppliedQuery("");
            }}
          >
            重置
          </button>
        </div>
      </form>

      <PinnedTable pinLeft={1} pinRight={1}>
        <thead>
          <tr>
            <th>到账日</th>
            <th>合同</th>
            <th>甲乙</th>
            <th>期次</th>
            <th className="ui-money">金额</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5}>
                <EmptyHint>
                  {appliedQuery
                    ? "没有匹配的回款。可以改关键词，或点重置看全部。"
                    : "还没有回款。打开某份合同，在「回款」页签登记确收。"}
                </EmptyHint>
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
                  <PartyStack a={row.party_a} b={row.party_b} />
                </td>
                <td>{row.schedule_name || "—"}</td>
                <td className="ui-money">{money(row.amount)}</td>
              </tr>
            ))
          )}
        </tbody>
      </PinnedTable>
      <Pager page={page} total={total} onPage={setPage} />
    </AppShell>
  );
}
