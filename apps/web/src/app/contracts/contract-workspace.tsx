"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { FileActions, FilePreview } from "@/components/file-preview";
import { EmptyHint, Field, FormError, PageHeader } from "@/components/ui";
import { api, money } from "@/lib/api";
import {
  CONTRACT_STATUS_LABEL,
  type Collection,
  type Contract,
  type ContractFile,
  type Invoice,
  type PaymentSchedule,
} from "@/lib/types";

type Tab = "fields" | "files" | "invoices" | "payments";

export function ContractWorkspace({
  contractId,
  initialTab = "fields",
}: {
  contractId: number;
  initialTab?: Tab;
}) {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>(initialTab);
  const [contract, setContract] = useState<Contract | null>(null);
  const [files, setFiles] = useState<ContractFile[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [schedules, setSchedules] = useState<PaymentSchedule[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    const [nextContract, nextFiles, nextInvoices, nextSchedules, nextCollections] = await Promise.all([
      api<Contract>(`/api/v1/contracts/${contractId}`),
      api<ContractFile[]>(`/api/v1/contracts/${contractId}/files`),
      api<Invoice[]>("/api/v1/invoices"),
      api<PaymentSchedule[]>(`/api/v1/contracts/${contractId}/schedules`),
      api<Collection[]>(`/api/v1/contracts/${contractId}/collections`),
    ]);
    setContract(nextContract);
    setFiles(nextFiles);
    setInvoices(nextInvoices.filter((item) => item.contract_id === contractId));
    setSchedules(nextSchedules);
    setCollections(nextCollections);
  }

  useEffect(() => {
    reload().catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
  }, [contractId]);

  async function saveFields(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!contract) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/contracts/${contractId}`, {
        method: "PUT",
        body: JSON.stringify({
          ...contract,
          contract_no: contract.contract_no,
          signed_at: contract.signed_at || null,
          start_date: contract.start_date || null,
          end_date: contract.end_date || null,
          notes: contract.notes || null,
        }),
      });
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete() {
    if (!window.confirm("确定删除这份合同？若已有关联发票，需要先处理发票。")) return;
    await api(`/api/v1/contracts/${contractId}`, { method: "DELETE" });
    router.push("/contracts");
  }

  if (!contract) {
    return (
      <AppShell>
        <p className="text-body text-mid-gray">{error || "加载中…"}</p>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Contracts"
        title={contract.title}
        description={`编号 ${contract.contract_no || "未编号（内部 ID " + contract.id + "）"} · 合同额 ${money(contract.amount)} · 已开票 ${money(contract.billed_amount)} · 已回款 ${money(contract.collected_amount)}`}
        action={
          <Link href={`/invoices/new?contract=${contractId}`} className="ui-btn ui-btn-primary">
            新建发票
          </Link>
        }
      />
      {error ? (
        <div className="mb-6">
          <FormError message={error} />
        </div>
      ) : null}

      <div className="mb-6 flex flex-wrap gap-3">
        {(
          [
            ["fields", "要素"],
            ["files", "附件"],
            ["invoices", "发票"],
            ["payments", "回款"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={tab === key ? "ui-btn ui-btn-primary" : "ui-btn ui-btn-secondary"}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "fields" ? (
        <form onSubmit={saveFields} className="ui-card max-w-2xl space-y-5 p-6">
          <Field label="合同名称">
            <input
              required
              value={contract.title}
              onChange={(e) => setContract({ ...contract, title: e.target.value })}
              className="ui-input"
            />
          </Field>
          <Field label="合同编号（可空）">
            <input
              value={contract.contract_no ?? ""}
              onChange={(e) => setContract({ ...contract, contract_no: e.target.value || null })}
              className="ui-input"
              placeholder="没有编号可以留空"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="甲方主体">
              <input
                value={contract.party_a}
                onChange={(e) => setContract({ ...contract, party_a: e.target.value })}
                className="ui-input"
              />
            </Field>
            <Field label="乙方主体">
              <input
                value={contract.party_b}
                onChange={(e) => setContract({ ...contract, party_b: e.target.value })}
                className="ui-input"
              />
            </Field>
          </div>
          <Field label="产品 / 服务名称">
            <input
              value={contract.subject_name ?? ""}
              onChange={(e) => setContract({ ...contract, subject_name: e.target.value })}
              className="ui-input"
              placeholder="甲方采购、或乙方向甲方销售的产品或服务"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="合同总金额（元）">
              <input
                required
                type="number"
                step="0.01"
                min="0"
                value={contract.amount}
                onChange={(e) => setContract({ ...contract, amount: e.target.value })}
                className="ui-input"
              />
            </Field>
            <Field label="签订时间">
              <input
                type="date"
                value={contract.signed_at ?? ""}
                onChange={(e) => setContract({ ...contract, signed_at: e.target.value || null })}
                className="ui-input"
              />
            </Field>
            <Field label="状态">
              <select
                value={contract.status}
                onChange={(e) => setContract({ ...contract, status: e.target.value })}
                className="ui-input"
              >
                {Object.entries(CONTRACT_STATUS_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="履约开始">
              <input
                type="date"
                value={contract.start_date ?? ""}
                onChange={(e) => setContract({ ...contract, start_date: e.target.value || null })}
                className="ui-input"
              />
            </Field>
            <Field label="履约结束">
              <input
                type="date"
                value={contract.end_date ?? ""}
                onChange={(e) => setContract({ ...contract, end_date: e.target.value || null })}
                className="ui-input"
              />
            </Field>
          </div>
          <Field label="备注">
            <textarea
              value={contract.notes ?? ""}
              onChange={(e) => setContract({ ...contract, notes: e.target.value })}
              rows={4}
              className="ui-input"
            />
          </Field>
          <div className="flex items-center gap-3 pt-3">
            <button type="submit" disabled={busy} className="ui-btn ui-btn-primary">
              保存要素
            </button>
            <button type="button" onClick={onDelete} className="ui-btn ui-btn-danger">
              删除
            </button>
          </div>
        </form>
      ) : null}

      {tab === "files" ? (
        <div className="space-y-4">
          {files.length === 0 ? <p className="text-body text-mid-gray">还没有附件。请走上传解析。</p> : null}
          {files.map((item) => (
            <article key={item.id} className="ui-card p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-medium text-ink">{item.original_name}</p>
                  <p className="mt-2 text-body text-mid-gray">
                    {item.source === "scanned" ? "扫描件" : "电子 PDF"} · {item.doc_type} · {item.parse_status}
                  </p>
                  {item.error_message ? <p className="mt-2 text-body text-ember">{item.error_message}</p> : null}
                </div>
                <FileActions fileId={item.id} />
              </div>
              <FilePreview fileId={item.id} name={item.original_name} />
            </article>
          ))}
        </div>
      ) : null}

      {tab === "invoices" ? (
        <div className="ui-card overflow-x-auto">
          <table className="ui-table">
            <thead>
              <tr>
                <th>发票</th>
                <th>代码 / 号码</th>
                <th>金额</th>
              </tr>
            </thead>
            <tbody>
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={3}>
                    <EmptyHint>还没有发票。识别草稿会列在这里，也可以右上角新建。</EmptyHint>
                  </td>
                </tr>
              ) : (
                invoices.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link href={`/invoices/${item.id}`} className="font-medium hover:underline">
                        {item.title}
                      </Link>
                    </td>
                    <td>
                      {item.invoice_code || "—"} / {item.invoice_no}
                    </td>
                    <td>{money(item.amount, item.currency)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "payments" ? (
        <PaymentsPanel
          contractId={contractId}
          schedules={schedules}
          collections={collections}
          onChanged={reload}
        />
      ) : null}
    </AppShell>
  );
}

function localToday(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function RowActions({
  onEdit,
  onDelete,
}: {
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <span className="flex shrink-0 items-center gap-3">
      <button type="button" onClick={onEdit} className="text-body font-medium text-ink underline-offset-4 hover:underline">
        编辑
      </button>
      <button
        type="button"
        onClick={onDelete}
        className="text-body font-medium text-ember underline-offset-4 hover:underline"
      >
        删除
      </button>
    </span>
  );
}

function ScheduleRow({
  item,
  contractId,
  onChanged,
  onError,
}: {
  item: PaymentSchedule;
  contractId: number;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(item.name);
  const [amount, setAmount] = useState(item.amount);

  useEffect(() => {
    setName(item.name);
    setAmount(item.amount);
  }, [item.name, item.amount]);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api(`/api/v1/contracts/${contractId}/schedules/${item.id}`, {
        method: "PUT",
        body: JSON.stringify({
          name,
          amount,
          due_date: item.due_date,
          notes: item.notes,
        }),
      });
      setEditing(false);
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "保存失败");
    }
  }

  async function remove() {
    if (!window.confirm("确定删除这一期回款计划？若已经挂了发票或到账，需要先处理那些记录。")) return;
    try {
      await api(`/api/v1/contracts/${contractId}/schedules/${item.id}`, { method: "DELETE" });
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <li className="rounded-[10px] bg-canvas px-4 py-3 text-body">
      {editing ? (
        <form onSubmit={save} className="flex flex-wrap items-center gap-3">
          <input value={name} onChange={(e) => setName(e.target.value)} className="ui-input w-32" required />
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="ui-input w-32"
            required
          />
          <button type="submit" className="ui-btn ui-btn-primary">
            保存
          </button>
          <button type="button" onClick={() => setEditing(false)} className="ui-btn ui-btn-secondary">
            取消
          </button>
        </form>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span>
            {item.period_no}. {item.name} · 计划 {money(item.amount)} · 已回 {money(item.collected_amount)}
          </span>
          <RowActions onEdit={() => setEditing(true)} onDelete={remove} />
        </div>
      )}
    </li>
  );
}

function CollectionRow({
  item,
  contractId,
  schedules,
  onChanged,
  onError,
}: {
  item: Collection;
  contractId: number;
  schedules: PaymentSchedule[];
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState(item.amount);
  const [receivedAt, setReceivedAt] = useState(item.received_at ?? "");
  const [scheduleId, setScheduleId] = useState(item.schedule_id ? String(item.schedule_id) : "");
  const scheduleName = schedules.find((row) => row.id === item.schedule_id)?.name;

  useEffect(() => {
    setAmount(item.amount);
    setReceivedAt(item.received_at ?? "");
    setScheduleId(item.schedule_id ? String(item.schedule_id) : "");
  }, [item.amount, item.received_at, item.schedule_id]);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api(`/api/v1/contracts/${contractId}/collections/${item.id}`, {
        method: "PUT",
        body: JSON.stringify({
          amount,
          received_at: receivedAt || null,
          schedule_id: scheduleId ? Number(scheduleId) : null,
          notes: item.notes,
        }),
      });
      setEditing(false);
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "保存失败");
    }
  }

  async function remove() {
    if (!window.confirm("确定删除这笔到账？删除后合同已回款金额会重新计算。")) return;
    try {
      await api(`/api/v1/contracts/${contractId}/collections/${item.id}`, { method: "DELETE" });
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <li className="rounded-[10px] bg-canvas px-4 py-3 text-body">
      {editing ? (
        <form onSubmit={save} className="flex flex-wrap items-center gap-3">
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="ui-input w-32"
            required
          />
          <input type="date" value={receivedAt} onChange={(e) => setReceivedAt(e.target.value)} className="ui-input w-40" />
          <select value={scheduleId} onChange={(e) => setScheduleId(e.target.value)} className="ui-input w-40">
            <option value="">不指定期次</option>
            {schedules.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name}
              </option>
            ))}
          </select>
          <button type="submit" className="ui-btn ui-btn-primary">
            保存
          </button>
          <button type="button" onClick={() => setEditing(false)} className="ui-btn ui-btn-secondary">
            取消
          </button>
        </form>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span>
            {money(item.amount)} · {item.received_at || "未填日期"}
            {scheduleName ? ` · ${scheduleName}` : ""}
          </span>
          <RowActions onEdit={() => setEditing(true)} onDelete={remove} />
        </div>
      )}
    </li>
  );
}

function PaymentsPanel({
  contractId,
  schedules,
  collections,
  onChanged,
}: {
  contractId: number;
  schedules: PaymentSchedule[];
  collections: Collection[];
  onChanged: () => Promise<void>;
}) {
  const [name, setName] = useState("第二期");
  const [amount, setAmount] = useState("0");
  const [received, setReceived] = useState("0");
  const [receivedAt, setReceivedAt] = useState(localToday);
  const [scheduleId, setScheduleId] = useState("");
  const [error, setError] = useState("");

  async function addSchedule(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api(`/api/v1/contracts/${contractId}/schedules`, {
        method: "POST",
        body: JSON.stringify({ name, amount }),
      });
      setAmount("0");
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "添加失败");
    }
  }

  async function addCollection(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api(`/api/v1/contracts/${contractId}/collections`, {
        method: "POST",
        body: JSON.stringify({
          amount: received,
          received_at: receivedAt || null,
          schedule_id: scheduleId ? Number(scheduleId) : null,
        }),
      });
      setReceived("0");
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "登记失败");
    }
  }

  return (
    <div className="space-y-6">
      {error ? <FormError message={error} /> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="ui-card p-6">
          <h3 className="heading-sm">回款计划</h3>
          <p className="mt-3 text-body text-mid-gray">一次性会自动生成一期；分期在这里加期数。输错了可以直接改或删。</p>
          <ul className="mt-5 space-y-2.5">
            {schedules.map((item) => (
              <ScheduleRow
                key={item.id}
                item={item}
                contractId={contractId}
                onChanged={onChanged}
                onError={setError}
              />
            ))}
          </ul>
          <form onSubmit={addSchedule} className="mt-5 flex flex-wrap gap-3">
            <input value={name} onChange={(e) => setName(e.target.value)} className="ui-input w-32" />
            <input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="ui-input w-32"
            />
            <button type="submit" className="ui-btn ui-btn-secondary">
              加一期
            </button>
          </form>
        </div>
        <div className="ui-card p-6">
          <h3 className="heading-sm">实际回款</h3>
          <p className="mt-3 text-body text-mid-gray">金额、日期、期次都可以事后修改；删掉后已回款会重新汇总。</p>
          <ul className="mt-5 space-y-2.5">
            {collections.map((item) => (
              <CollectionRow
                key={item.id}
                item={item}
                contractId={contractId}
                schedules={schedules}
                onChanged={onChanged}
                onError={setError}
              />
            ))}
          </ul>
          <form onSubmit={addCollection} className="mt-5 flex flex-wrap gap-3">
            <input
              type="number"
              step="0.01"
              min="0"
              value={received}
              onChange={(e) => setReceived(e.target.value)}
              className="ui-input w-32"
            />
            <input type="date" value={receivedAt} onChange={(e) => setReceivedAt(e.target.value)} className="ui-input w-40" />
            <select value={scheduleId} onChange={(e) => setScheduleId(e.target.value)} className="ui-input w-40">
              <option value="">不指定期次</option>
              {schedules.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <button type="submit" className="ui-btn ui-btn-primary">
              登记到账
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
