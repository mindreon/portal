"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { api, money } from "@/lib/api";
import type { Contract, Invoice } from "@/lib/types";

export default function HomePage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  useEffect(() => {
    Promise.all([api<Contract[]>("/api/v1/contracts"), api<Invoice[]>("/api/v1/invoices")]).then(
      ([nextContracts, nextInvoices]) => {
        setContracts(nextContracts);
        setInvoices(nextInvoices);
      },
    );
  }, []);

  const activeContracts = contracts.filter((item) => item.status === "active").length;
  const unpaidInvoices = invoices.filter((item) => item.status === "issued").length;

  return (
    <AppShell>
      <header className="mb-8">
        <p className="text-sm text-[#7a6a55]">今天要处理的事，都放在这一页。</p>
        <h2 className="mt-1 text-3xl font-semibold">工作台</h2>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        <StatCard title="合同总数" value={String(contracts.length)} href="/contracts" />
        <StatCard title="履约中" value={String(activeContracts)} href="/contracts" />
        <StatCard title="待收款发票" value={String(unpaidInvoices)} href="/invoices" />
      </section>

      <section className="mt-10 grid gap-8 lg:grid-cols-2">
        <RecentList
          title="最近合同"
          href="/contracts"
          rows={contracts.slice(0, 5).map((item) => ({
            id: item.id,
            title: item.title,
            meta: `${item.counterparty} · ${money(item.amount, item.currency)}`,
            href: `/contracts/${item.id}`,
          }))}
        />
        <RecentList
          title="最近发票"
          href="/invoices"
          rows={invoices.slice(0, 5).map((item) => ({
            id: item.id,
            title: item.title,
            meta: `${item.invoice_no} · ${money(item.amount, item.currency)}`,
            href: `/invoices/${item.id}`,
          }))}
        />
      </section>
    </AppShell>
  );
}

function StatCard({ title, value, href }: { title: string; value: string; href: string }) {
  return (
    <Link href={href} className="rounded-xl border border-[var(--line)] bg-[var(--card)] p-5 shadow-sm">
      <p className="text-sm text-[#7a6a55]">{title}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </Link>
  );
}

function RecentList({
  title,
  href,
  rows,
}: {
  title: string;
  href: string;
  rows: { id: number; title: string; meta: string; href: string }[];
}) {
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--card)] p-5">
      <div className="mb-4 flex items-end justify-between">
        <h3 className="text-xl font-semibold">{title}</h3>
        <Link href={href} className="text-sm text-[var(--accent)] hover:underline">
          查看全部
        </Link>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-[#7a6a55]">还没有数据。先新建一条试试看。</p>
      ) : (
        <ul className="space-y-3">
          {rows.map((row) => (
            <li key={row.id}>
              <Link href={row.href} className="block rounded-md px-1 py-1 hover:bg-[#f6f0e6]">
                <p className="font-medium">{row.title}</p>
                <p className="text-sm text-[#7a6a55]">{row.meta}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
