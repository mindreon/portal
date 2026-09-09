"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PinnedTable } from "@/components/pinned-table";
import { EmptyHint, PAGE_SIZE, PageHeader, Pager, PartyStack } from "@/components/ui";
import { api, money, withQuery } from "@/lib/api";
import type { CollectionPage, CollectionRow, ContractSummary } from "@/lib/types";

type Side = "in" | "out";

function parseSide(value: string | null): Side {
  return value === "out" ? "out" : "in";
}

export default function ContractBillsPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <p className="text-body text-mid-gray">加载中…</p>
        </AppShell>
      }
    >
      <BillsPageBody />
    </Suspense>
  );
}

function BillsPageBody() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const side = parseSide(searchParams.get("side"));
  const incoming = side === "in";

  const [rows, setRows] = useState<CollectionRow[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ContractSummary | null>(null);
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    const kind = incoming ? "receivable" : "payable";
    Promise.all([
      api<CollectionPage>(
        withQuery("/api/v1/contracts/payments", { q: appliedQuery, kind, page, page_size: PAGE_SIZE }),
      ),
      api<ContractSummary>("/api/v1/contracts/summary"),
    ])
      .then(([list, nextSummary]) => {
        if (cancelled) return;
        setRows(list.items);
        setTotal(list.total);
        setSummary(nextSummary);
        if (list.total > 0 && list.items.length === 0 && page > 1) {
          setPage(list.page > 1 ? list.page - 1 : 1);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [appliedQuery, incoming, page]);

  function goSide(next: Side) {
    setPage(1);
    router.replace(next === "out" ? "/contracts/bills?side=out" : "/contracts/bills");
  }

  function onSearch(event: React.FormEvent) {
    event.preventDefault();
    setPage(1);
    setAppliedQuery(query.trim());
  }

  const copy = incoming
    ? {
        title: "账单",
        description: "迈能同行是乙方时，钱是收进来的。这里只看应收账款，不会和付出去的加在一起。",
        total: "应收账款",
        settled: "已收进来",
        leftover: "还没收齐",
        date: "收款日",
        emptySearch: "没有匹配的收款记录。可以改关键词，或点重置看全部。",
        empty: "还没有收进来的账单。打开销售合同，在「收款」页签里登记。",
        amount: summary?.receivable_amount ?? "0",
        settledAmount: summary?.receivable_collected ?? "0",
        leftoverAmount: summary?.receivable_outstanding ?? "0",
      }
    : {
        title: "账单",
        description: "迈能同行是甲方时，钱是付出去的。这里只看应付账款，不会和收进来的加在一起。",
        total: "应付账款",
        settled: "已付出去",
        leftover: "还没付齐",
        date: "付款日",
        emptySearch: "没有匹配的付款记录。可以改关键词，或点重置看全部。",
        empty: "还没有付出去的账单。打开采购合同，在「付款」页签里登记。",
        amount: summary?.payable_amount ?? "0",
        settledAmount: summary?.payable_paid ?? "0",
        leftoverAmount: summary?.payable_outstanding ?? "0",
      };

  return (
    <AppShell>
      <PageHeader title={copy.title} description={copy.description} />

      <div className="mb-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => goSide("in")}
          className={incoming ? "ui-btn ui-btn-primary" : "ui-btn ui-btn-secondary"}
        >
          收进来的
        </button>
        <button
          type="button"
          onClick={() => goSide("out")}
          className={!incoming ? "ui-btn ui-btn-primary" : "ui-btn ui-btn-secondary"}
        >
          付出去的
        </button>
      </div>

      <section className="mb-8 grid gap-6 sm:grid-cols-3">
        <StatBlock label={copy.total} value={money(copy.amount)} />
        <StatBlock label={copy.settled} value={money(copy.settledAmount)} />
        <StatBlock label={copy.leftover} value={money(copy.leftoverAmount)} />
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
            <th>{copy.date}</th>
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
                <EmptyHint>{appliedQuery ? copy.emptySearch : copy.empty}</EmptyHint>
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

function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="ui-card min-w-0 p-6">
      <p className="eyebrow">{label}</p>
      <p className="stat-value mt-3">{value}</p>
    </div>
  );
}
