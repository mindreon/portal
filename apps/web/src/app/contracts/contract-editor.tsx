"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Field, FormError, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { CONTRACT_STATUS_LABEL, type Contract } from "@/lib/types";

const EMPTY = {
  title: "",
  contract_no: "",
  counterparty: "",
  amount: "0",
  currency: "CNY",
  status: "draft",
  start_date: "",
  end_date: "",
  notes: "",
};

export function ContractEditor({ contractId }: { contractId?: number }) {
  const router = useRouter();
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!contractId) return;
    api<Contract>(`/api/v1/contracts/${contractId}`).then((item) => {
      setForm({
        title: item.title,
        contract_no: item.contract_no,
        counterparty: item.counterparty,
        amount: item.amount,
        currency: item.currency,
        status: item.status,
        start_date: item.start_date ?? "",
        end_date: item.end_date ?? "",
        notes: item.notes ?? "",
      });
    });
  }, [contractId]);

  function update(name: keyof typeof EMPTY, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const payload = {
      ...form,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      notes: form.notes || null,
    };
    try {
      if (contractId) {
        await api(`/api/v1/contracts/${contractId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await api("/api/v1/contracts", { method: "POST", body: JSON.stringify(payload) });
      }
      router.push("/contracts");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
      setBusy(false);
    }
  }

  async function onDelete() {
    if (!contractId || !window.confirm("确定删除这份合同？若已有关联发票，需要先处理发票。")) return;
    await api(`/api/v1/contracts/${contractId}`, { method: "DELETE" });
    router.push("/contracts");
  }

  return (
    <AppShell>
      <PageHeader eyebrow="Contracts" title={contractId ? "编辑合同" : "新建合同"} />
      <form onSubmit={onSubmit} className="ui-card max-w-2xl space-y-4 p-8">
        <FormError message={error} />
        <Field label="合同名称">
          <input required value={form.title} onChange={(e) => update("title", e.target.value)} className="ui-input" />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="合同编号">
            <input required value={form.contract_no} onChange={(e) => update("contract_no", e.target.value)} className="ui-input" />
          </Field>
          <Field label="对方名称">
            <input required value={form.counterparty} onChange={(e) => update("counterparty", e.target.value)} className="ui-input" />
          </Field>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="金额">
            <input required type="number" step="0.01" min="0" value={form.amount} onChange={(e) => update("amount", e.target.value)} className="ui-input" />
          </Field>
          <Field label="币种">
            <input value={form.currency} onChange={(e) => update("currency", e.target.value)} className="ui-input" />
          </Field>
          <Field label="状态">
            <select value={form.status} onChange={(e) => update("status", e.target.value)} className="ui-input">
              {Object.entries(CONTRACT_STATUS_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="开始日期">
            <input type="date" value={form.start_date} onChange={(e) => update("start_date", e.target.value)} className="ui-input" />
          </Field>
          <Field label="结束日期">
            <input type="date" value={form.end_date} onChange={(e) => update("end_date", e.target.value)} className="ui-input" />
          </Field>
        </div>
        <Field label="备注">
          <textarea value={form.notes} onChange={(e) => update("notes", e.target.value)} rows={4} className="ui-input" />
        </Field>
        <div className="flex items-center gap-3 pt-2">
          <button type="submit" disabled={busy} className="ui-btn ui-btn-primary">
            保存
          </button>
          {contractId ? (
            <button type="button" onClick={onDelete} className="text-body-sm font-medium text-slate hover:underline">
              删除
            </button>
          ) : null}
        </div>
      </form>
    </AppShell>
  );
}
