"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Icon, ModuleIconTile, type IconName } from "@/components/icons";
import { PageHeader } from "@/components/ui";
import { api, money } from "@/lib/api";
import { useCurrentUser } from "@/lib/current-user";
import type { ContractSummary, InvoiceSummary } from "@/lib/types";

export default function HomePage() {
  const { ready, modules, canAccess } = useCurrentUser();
  const [contractSummary, setContractSummary] = useState<ContractSummary | null>(null);
  const [invoiceSummary, setInvoiceSummary] = useState<InvoiceSummary | null>(null);

  useEffect(() => {
    if (!ready) return;
    const jobs: Promise<void>[] = [];
    if (canAccess("contracts")) {
      jobs.push(api<ContractSummary>("/api/v1/contracts/summary").then(setContractSummary));
    }
    if (canAccess("invoices")) {
      jobs.push(api<InvoiceSummary>("/api/v1/invoices/summary").then(setInvoiceSummary));
    }
    Promise.all(jobs).catch(() => undefined);
  }, [ready, canAccess]);

  const showContracts = canAccess("contracts");
  const showInvoices = canAccess("invoices");

  return (
    <AppShell>
      <PageHeader
        title="工作台"
        description="每个业务是一间独立的房间。菜单按你的权限显示；管理员在左下角「权限管理」里给同事勾选房间。"
      />

      <section className="grid gap-6 sm:grid-cols-2">
        {modules.map((item) => (
          <Link key={item.id} href={item.href} className="ui-card block p-6">
            <ModuleIconTile moduleId={item.id} />
            <h3 className="heading-sm mt-4">{item.name}</h3>
            <p className="mt-3 text-body text-mid-gray">{item.summary}</p>
            <p className="mt-6 inline-flex items-center gap-1.5 text-body font-medium text-ink">
              进入
              <Icon name="arrow-right" size={16} />
            </p>
          </Link>
        ))}
      </section>

      {showContracts || showInvoices ? (
        <section className="mt-8 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {showContracts ? (
            <StatCard title="合同总数" value={String(contractSummary?.count ?? 0)} href="/contracts" icon="file-text" />
          ) : null}
          {showContracts ? (
            <StatCard
              title="应收账款"
              value={money(contractSummary?.receivable_amount ?? 0)}
              href="/contracts"
              icon="file-text"
            />
          ) : null}
          {showContracts ? (
            <StatCard
              title="应付账款"
              value={money(contractSummary?.payable_amount ?? 0)}
              href="/contracts"
              icon="file-text"
            />
          ) : null}
          {showInvoices ? (
            <StatCard title="待收款发票" value={String(invoiceSummary?.issued_count ?? 0)} href="/invoices" icon="receipt" />
          ) : null}
        </section>
      ) : null}
    </AppShell>
  );
}

function StatCard({
  title,
  value,
  href,
  icon,
}: {
  title: string;
  value: string;
  href: string;
  icon: IconName;
}) {
  return (
    <Link href={href} className="ui-card block min-w-0 overflow-hidden p-6">
      <p className="flex items-center gap-2 text-[13px] font-medium text-mid-gray">
        <Icon name={icon} size={16} className={icon === "receipt" ? "text-teal" : "text-brand"} />
        {title}
      </p>
      <p className="stat-value mt-3">{value}</p>
    </Link>
  );
}
