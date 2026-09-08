"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PageHeader, TextLink } from "@/components/ui";
import { api, money } from "@/lib/api";
import { useCurrentUser } from "@/lib/current-user";
import type { Contract, Invoice } from "@/lib/types";

export default function HomePage() {
  const { ready, modules, canAccess } = useCurrentUser();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  useEffect(() => {
    if (!ready) return;
    const jobs: Promise<void>[] = [];
    if (canAccess("contracts")) {
      jobs.push(api<Contract[]>("/api/v1/contracts").then(setContracts));
    }
    if (canAccess("invoices")) {
      jobs.push(api<Invoice[]>("/api/v1/invoices").then(setInvoices));
    }
    Promise.all(jobs).catch(() => undefined);
  }, [ready, canAccess]);

  const activeContracts = contracts.filter((item) => item.status === "active").length;
  const unpaidInvoices = invoices.filter((item) => item.status === "issued").length;
  const showContracts = canAccess("contracts");
  const showInvoices = canAccess("invoices");

  return (
    <AppShell>
      <PageHeader
        eyebrow="Workbench"
        title="工作台"
        description="每个业务是一间独立的房间。菜单按你的权限显示；管理员在左下角「权限管理」里给同事勾选房间。"
      />

      <section className="grid gap-6 sm:grid-cols-2">
        {modules.map((item) => (
          <Link key={item.id} href={item.href} className="ui-card block p-6">
            <p className="eyebrow">{item.hint}</p>
            <h3 className="heading-sm mt-3">{item.name}</h3>
            <p className="mt-3 text-body text-mid-gray">{item.summary}</p>
            <p className="mt-6 text-body font-medium text-ink">进入 →</p>
          </Link>
        ))}
      </section>

      {showContracts || showInvoices ? (
        <section className="mt-8 grid gap-6 sm:grid-cols-3">
          {showContracts ? <StatCard title="合同总数" value={String(contracts.length)} href="/contracts" /> : null}
          {showContracts ? <StatCard title="履约中" value={String(activeContracts)} href="/contracts" /> : null}
          {showInvoices ? <StatCard title="待收款发票" value={String(unpaidInvoices)} href="/invoices" /> : null}
        </section>
      ) : null}

      <section className={`mt-8 grid gap-6 ${showContracts && showInvoices ? "lg:grid-cols-2" : ""}`}>
        {showContracts ? (
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
        ) : null}
        {showInvoices ? (
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
        ) : null}
      </section>
    </AppShell>
  );
}

function StatCard({ title, value, href }: { title: string; value: string; href: string }) {
  return (
    <Link href={href} className="ui-card block min-w-0 overflow-hidden p-6">
      <p className="eyebrow">{title}</p>
      <p className="stat-value mt-3">{value}</p>
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
    <div className="ui-card p-6">
      <div className="mb-5 flex items-end justify-between gap-4">
        <h3 className="heading-sm">{title}</h3>
        <TextLink href={href}>查看全部</TextLink>
      </div>
      {rows.length === 0 ? (
        <p className="text-body text-mid-gray">{empty}</p>
      ) : (
        <ul className="space-y-1.5">
          {rows.map((row) => (
            <li key={row.id}>
              <Link href={row.href} className="block rounded-[10px] px-3 py-3 hover:bg-canvas">
                <p className="font-medium text-ink">{row.title}</p>
                <p className="mt-1 text-body text-mid-gray">{row.meta}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
