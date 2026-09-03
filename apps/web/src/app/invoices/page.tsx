"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { api, money } from "@/lib/api";
import type { Invoice } from "@/lib/types";

export default function InvoicesPage() {
  const [rows, setRows] = useState<Invoice[]>([]);

  useEffect(() => {
    api<Invoice[]>("/api/v1/invoices").then(setRows);
  }, []);

  return (
    <AppShell>
      <div className="mb-6 flex items-end justify-between">
        <div>
          <p className="text-sm text-[#7a6a55]">发票可以独立存在，也可以关联到一份合同。</p>
          <h2 className="mt-1 text-3xl font-semibold">发票</h2>
        </div>
        <Link
          href="/invoices/new"
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-white hover:bg-[var(--accent-dark)]"
        >
          新建发票
        </Link>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--card)]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#efe7d8] text-[#5c4c38]">
            <tr>
              <th className="px-4 py-3 font-medium">发票</th>
              <th className="px-4 py-3 font-medium">对方</th>
              <th className="px-4 py-3 font-medium">金额</th>
              <th className="px-4 py-3 font-medium">状态</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-[#7a6a55]">
                  还没有发票。点右上角新建第一条。
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-t border-[var(--line)]">
                  <td className="px-4 py-3">
                    <Link href={`/invoices/${row.id}`} className="font-medium hover:underline">
                      {row.title}
                    </Link>
                    <p className="text-xs text-[#7a6a55]">{row.invoice_no}</p>
                  </td>
                  <td className="px-4 py-3">{row.counterparty}</td>
                  <td className="px-4 py-3">{money(row.amount, row.currency)}</td>
                  <td className="px-4 py-3">
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
