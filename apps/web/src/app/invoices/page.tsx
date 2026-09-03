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
        action={
          <Link href="/invoices/new" className="ui-btn ui-btn-primary">
            新建发票
          </Link>
        }
      />
      <p className="-mt-4 mb-8 text-body-sm text-slate">
        独立模块。发票可以单独开，也可以在表单里选择关联某份合同。
      </p>

      <div className="ui-card overflow-hidden">
        <table className="w-full text-left text-body-sm">
          <thead className="text-slate">
            <tr>
              <th className="px-6 py-4 font-medium">发票</th>
              <th className="px-6 py-4 font-medium">对方</th>
              <th className="px-6 py-4 font-medium">金额</th>
              <th className="px-6 py-4 font-medium">状态</th>
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
                <tr key={row.id} className="border-t border-charcoal/15">
                  <td className="px-6 py-4">
                    <Link href={`/invoices/${row.id}`} className="font-medium hover:underline">
                      {row.title}
                    </Link>
                    <p className="text-[12px] text-slate">{row.invoice_no}</p>
                  </td>
                  <td className="px-6 py-4">{row.counterparty}</td>
                  <td className="px-6 py-4">{money(row.amount, row.currency)}</td>
                  <td className="px-6 py-4">
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
