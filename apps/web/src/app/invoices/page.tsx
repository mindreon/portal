"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PinnedTable } from "@/components/pinned-table";
import { StatusBadge } from "@/components/status-badge";
import { EmptyHint, PAGE_SIZE, PageHeader, Pager } from "@/components/ui";
import { api, money, withQuery } from "@/lib/api";
import type { Invoice, PageResult } from "@/lib/types";

export default function InvoicesPage() {
  const [rows, setRows] = useState<Invoice[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    api<PageResult<Invoice>>(
      withQuery("/api/v1/invoices", { q: appliedQuery, page, page_size: PAGE_SIZE }),
    )
      .then((list) => {
        if (cancelled) return;
        setRows(list.items);
        setTotal(list.total);
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
        title="发票"
        description="独立模块。发票可以单独开，不必先有合同。"
        action={
          <Link href="/invoices/new" className="ui-btn ui-btn-primary">
            新建发票
          </Link>
        }
      />

      <form onSubmit={onSearch} className="ui-card mb-6 flex flex-wrap items-end gap-4 p-6">
        <label className="min-w-[200px] flex-1 text-body">
          <span className="mb-2 block font-medium text-ink">搜索</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="发票名称、号码或对方"
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
            <th>发票</th>
            <th>对方</th>
            <th className="ui-money">金额</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={4}>
                <EmptyHint>
                  {appliedQuery ? "没有匹配的发票。可以改关键词，或点重置看全部。" : "还没有发票。点右上角新建第一条。"}
                </EmptyHint>
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <Link href={`/invoices/${row.id}`} className="font-medium hover:underline">
                    {row.title}
                  </Link>
                  <p className="mt-1 text-[12px] text-mid-gray">
                    {row.invoice_no.startsWith("UP-") ? "号码待填写" : row.invoice_no}
                    {row.has_file ? " · 有 PDF" : ""}
                  </p>
                </td>
                <td>{row.counterparty}</td>
                <td className="ui-money">{money(row.amount, row.currency)}</td>
                <td>
                  <StatusBadge kind="invoice" value={row.status} />
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
