"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PageHeader, TextLink } from "@/components/ui";
import { api, money } from "@/lib/api";
import { MODULES } from "@/lib/modules";
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
      <PageHeader eyebrow="Workbench" title="工作台" />
      <p className="-mt-3 mb-8 max-w-xl text-body text-mid-gray">
        每个业务是一间独立的房间。先选模块进去做事；房间之间默认不相通，要用时再从这里或 ⌘K 跳过去。
      </p>

      <section className="grid gap-5 sm:grid-cols-2">
        {MODULES.map((item) => (
          <Link key={item.id} href={item.href} className="ui-card block p-5">
            <p className="eyebrow">{item.hint}</p>
            <h3 className="heading-sm mt-2">{item.name}</h3>
            <p className="mt-2 text-body text-mid-gray">{item.summary}</p>
            <p className="mt-5 text-body font-medium text-ink">进入 →</p>
          </Link>
        ))}
      </section>

      <section className="mt-12 grid gap-2 sm:grid-cols-3">
        <StatCard title="合同总数" value={String(contracts.length)} href="/contracts" />
        <StatCard title="履约中" value={String(activeContracts)} href="/contracts" />
        <StatCard title="待收款发票" value={String(unpaidInvoices)} href="/invoices" />
      </section>

      <section className="mt-12 grid gap-5 lg:grid-cols-2">
        <RecentList
          title="合同"
          href="/contracts"
          empty="合同还是空的，进合同模块建第一条。"
          rows={contracts.slice(0, 5).map((item) => ({
            id: item.id,
            title: item.title,
            meta: `${item.counterparty} · ${money(item.amount, item.currency)}`,
            href: `/contracts/${item.id}`,
          }))}
        />
        <RecentList
          title="发票"
          href="/invoices"
          empty="发票还是空的，进发票模块建第一条。"
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
    <Link href={href} className="ui-card block p-5">
      <p className="eyebrow">{title}</p>
      <p className="stat-value mt-2">{value}</p>
    </Link>
  );
}

function RecentList({
  title,
  href,
  empty,
  rows,
}: {
  title: string;
  href: string;
  empty: string;
  rows: { id: number; title: string; meta: string; href: string }[];
}) {
  return (
    <div className="ui-card p-5">
      <div className="mb-4 flex items-end justify-between">
        <h3 className="heading-sm">{title}</h3>
        <TextLink href={href}>查看全部</TextLink>
      </div>
      {rows.length === 0 ? (
        <p className="text-body text-mid-gray">{empty}</p>
      ) : (
        <ul className="space-y-1">
          {rows.map((row) => (
            <li key={row.id}>
              <Link href={row.href} className="block rounded-[10px] px-2 py-2 hover:bg-canvas">
                <p className="font-medium text-ink">{row.title}</p>
                <p className="text-body text-mid-gray">{row.meta}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
