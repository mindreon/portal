"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { INVOICE_STATUS_LABEL, type Contract, type Invoice } from "@/lib/types";

const EMPTY = {
  title: "",
  invoice_no: "",
  counterparty: "",
  amount: "0",
  tax_amount: "0",
  currency: "CNY",
  status: "draft",
  issued_at: "",
  due_at: "",
  notes: "",
  contract_id: "",
};

export function InvoiceEditor({ invoiceId }: { invoiceId?: number }) {
  const router = useRouter();
  const [form, setForm] = useState(EMPTY);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Contract[]>("/api/v1/contracts").then(setContracts);
    if (!invoiceId) return;
    api<Invoice>(`/api/v1/invoices/${invoiceId}`).then((item) => {
      setForm({
        title: item.title,
        invoice_no: item.invoice_no,
        counterparty: item.counterparty,
        amount: item.amount,
        tax_amount: item.tax_amount,
        currency: item.currency,
        status: item.status,
        issued_at: item.issued_at ?? "",
        due_at: item.due_at ?? "",
        notes: item.notes ?? "",
        contract_id: item.contract_id ? String(item.contract_id) : "",
      });
    });
  }, [invoiceId]);

  function update(name: keyof typeof EMPTY, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const payload = {
      ...form,
      issued_at: form.issued_at || null,
      due_at: form.due_at || null,
      notes: form.notes || null,
      contract_id: form.contract_id ? Number(form.contract_id) : null,
    };
    try {
      if (invoiceId) {
        await api(`/api/v1/invoices/${invoiceId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await api("/api/v1/invoices", { method: "POST", body: JSON.stringify(payload) });
      }
      router.push("/invoices");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
      setBusy(false);
    }
  }

  async function onDelete() {
    if (!invoiceId || !window.confirm("确定删除这张发票？")) return;
    await api(`/api/v1/invoices/${invoiceId}`, { method: "DELETE" });
    router.push("/invoices");
  }

  return (
    <AppShell>
      <h2 className="mb-6 text-3xl font-semibold">{invoiceId ? "编辑发票" : "新建发票"}</h2>
      <form onSubmit={onSubmit} className="max-w-2xl space-y-4 rounded-xl border border-[var(--line)] bg-[var(--card)] p-6">
        {error ? <p className="rounded-md bg-[#f8e8e4] px-3 py-2 text-sm text-[#8a3030]">{error}</p> : null}
        <Field label="发票名称">
          <input required value={form.title} onChange={(e) => update("title", e.target.value)} className={inputClass} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="发票编号">
            <input required value={form.invoice_no} onChange={(e) => update("invoice_no", e.target.value)} className={inputClass} />
          </Field>
          <Field label="对方名称">
            <input required value={form.counterparty} onChange={(e) => update("counterparty", e.target.value)} className={inputClass} />
          </Field>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="金额">
            <input required type="number" step="0.01" min="0" value={form.amount} onChange={(e) => update("amount", e.target.value)} className={inputClass} />
          </Field>
          <Field label="税额">
            <input required type="number" step="0.01" min="0" value={form.tax_amount} onChange={(e) => update("tax_amount", e.target.value)} className={inputClass} />
          </Field>
          <Field label="状态">
            <select value={form.status} onChange={(e) => update("status", e.target.value)} className={inputClass}>
              {Object.entries(INVOICE_STATUS_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="开票日期">
            <input type="date" value={form.issued_at} onChange={(e) => update("issued_at", e.target.value)} className={inputClass} />
          </Field>
          <Field label="到期日期">
            <input type="date" value={form.due_at} onChange={(e) => update("due_at", e.target.value)} className={inputClass} />
          </Field>
        </div>
        <Field label="关联合同（可选）">
          <select value={form.contract_id} onChange={(e) => update("contract_id", e.target.value)} className={inputClass}>
            <option value="">不关联</option>
            {contracts.map((item) => (
              <option key={item.id} value={item.id}>
                {item.contract_no} · {item.title}
              </option>
            ))}
          </select>
        </Field>
        <Field label="备注">
          <textarea value={form.notes} onChange={(e) => update("notes", e.target.value)} rows={4} className={inputClass} />
        </Field>
        <div className="flex items-center gap-3 pt-2">
          <button type="submit" disabled={busy} className="rounded-lg bg-[var(--accent)] px-4 py-2 text-white hover:bg-[var(--accent-dark)] disabled:opacity-60">
            保存
          </button>
          {invoiceId ? (
            <button type="button" onClick={onDelete} className="text-sm text-[#8a3030] hover:underline">
              删除
            </button>
          ) : null}
        </div>
      </form>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-[#5c4c38]">{label}</span>
      {children}
    </label>
  );
}

const inputClass = "w-full rounded-md border border-[var(--line)] bg-white px-3 py-2";
