"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { EmptyHint, PageHeader } from "@/components/ui";
import { api, money } from "@/lib/api";
import type { Invoice } from "@/lib/types";

export default function InvoicesPage() {
  const [rows, setRows] = useState<Invoice[]>([]);

  useEffect(() => {
    api<Invoice[]>("/api/v1/invoices").then(setRows);
  }, []);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Invoices"
        title="发票"
        description="独立模块。发票可以单独开，也可以在表单里选择关联某份合同。"
        action={
          <Link href="/invoices/new" className="ui-btn ui-btn-primary">
            新建发票
          </Link>
        }
      />

      <div className="ui-card overflow-x-auto">
        <table className="ui-table">
          <thead>
            <tr>
              <th>发票</th>
              <th>对方</th>
              <th>金额</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4}>
                  <EmptyHint>还没有发票。点右上角新建第一条。</EmptyHint>
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <Link href={`/invoices/${row.id}`} className="font-medium hover:underline">
                      {row.title}
                    </Link>
                    <p className="mt-1 text-[12px] text-mid-gray">{row.invoice_no}</p>
                  </td>
                  <td>{row.counterparty}</td>
                  <td>{money(row.amount, row.currency)}</td>
                  <td>
                    <StatusBadge kind="invoice" value={row.status} />
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
