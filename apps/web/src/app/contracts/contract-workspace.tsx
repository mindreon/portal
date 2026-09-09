"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { InvoicesPanel, UploadInvoiceButton } from "./invoices-panel";
import { AppShell } from "@/components/app-shell";
import { FileActions, FilePreview } from "@/components/file-preview";
import { PinnedTable } from "@/components/pinned-table";
import { StatusBadge } from "@/components/status-badge";
import { EmptyHint, Field, FormError, PageHeader } from "@/components/ui";
import { api, money, withQuery } from "@/lib/api";
import { useImportLive } from "@/lib/live";
import {
  ACCOUNT_KIND_LABEL,
  CONTRACT_STATUS_LABEL,
  paymentWords,
  type Collection,
  type Contract,
  type ContractFile,
  type Invoice,
  type PageResult,
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
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    const [nextContract, nextFiles, nextInvoices, nextSchedules, nextCollections] = await Promise.all([
      api<Contract>(`/api/v1/contracts/${contractId}`),
      api<ContractFile[]>(`/api/v1/contracts/${contractId}/files`),
      api<PageResult<Invoice>>(
        withQuery("/api/v1/invoices", { contract_id: contractId, page: 1, page_size: 100 }),
      ),
      api<PaymentSchedule[]>(`/api/v1/contracts/${contractId}/schedules`),
      api<Collection[]>(`/api/v1/contracts/${contractId}/collections`),
    ]);
    setContract(nextContract);
    setFiles(nextFiles);
    setInvoices(nextInvoices.items);
    setSchedules(nextSchedules);
    setCollections(nextCollections);
  }

  useEffect(() => {
    reload().catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
  }, [contractId]);

  const parsing = contract ? contract.parse_status === "pending" || contract.parse_status === "processing" : false;
  useImportLive(parsing, () => {
    reload().catch(() => undefined);
  });

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

  const words = paymentWords(contract.account_kind);
  const accountHint =
    contract.account_kind === "receivable"
      ? "我方是乙方，合同金额记应收账款。"
      : contract.account_kind === "payable"
        ? "我方是甲方，合同金额记应付账款。"
        : "甲乙双方里还没有识别到迈能同行，账款类型暂未判定。";

  return (
    <AppShell>
      <PageHeader
        title={contract.title}
        description={`${contract.source_filename ? `文件 ${contract.source_filename} · ` : ""}编号 ${contract.contract_no || "未编号（内部 ID " + contract.id + "）"} · ${ACCOUNT_KIND_LABEL[contract.account_kind] ?? ACCOUNT_KIND_LABEL[""]} ${money(contract.amount)} · 已开票 ${money(contract.billed_amount)} · ${words.settled} ${money(contract.collected_amount)}`}
        action={
          tab === "invoices" ? (
            <UploadInvoiceButton
              contractId={contractId}
              onUploaded={async (result) => {
                setError("");
                setNotice(result.warning_text || "");
                await reload();
              }}
              onError={(message) => {
                setNotice("");
                setError(message);
              }}
            />
          ) : (
            <Link href={`/invoices/new?contract=${contractId}`} className="ui-btn ui-btn-primary">
              新建发票
            </Link>
          )
        }
      />
      {error ? (
        <div className="mb-6">
          <FormError message={error} />
        </div>
      ) : null}
      {notice ? <p className="mb-6 text-body text-mid-gray">{notice}</p> : null}
      {contract.parse_status === "pending" || contract.parse_status === "processing" ? (
        <p className="mb-6 flex flex-wrap items-center gap-3 text-body text-mid-gray">
          <StatusBadge kind="parse" value={contract.parse_status} />
          正在后台识别这份合同，识别完会自动更新。刷新不会中断。
        </p>
      ) : null}
      {contract.parse_status === "failed" ? (
        <p className="mb-6 flex flex-wrap items-center gap-3 text-body text-mid-gray">
          <StatusBadge kind="parse" value={contract.parse_status} />
          识别没完成，请对照附件手工核对要素。
        </p>
      ) : null}

      <div className="mb-6 flex flex-wrap gap-3">
        {(
          [
            ["fields", "要素"],
            ["files", "附件"],
            ["invoices", "发票"],
            ["payments", words.tab],
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
          <p className="text-body text-mid-gray">{accountHint}</p>
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
        <InvoicesPanel
          contractId={contractId}
          invoices={invoices}
          onChanged={reload}
          onError={(message) => {
            setNotice("");
            setError(message);
          }}
          onNotice={(message) => {
            setError("");
            setNotice(message);
          }}
        />
      ) : null}

      {tab === "payments" ? (
        <PaymentsPanel
          contractId={contractId}
          accountKind={contract.account_kind}
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

function nextPeriodName(count: number): string {
  return count === 0 ? "一次性" : `第${count + 1}期`;
}

/** 这一期还差多少没回。已经齐了就填 0，避免误登记一笔重复的。 */
function leftover(item: PaymentSchedule): string {
  const left = Number(item.amount) - Number(item.collected_amount);
  if (!Number.isFinite(left) || left <= 0) return "0";
  return String(left);
}

function latestReceivedAt(rows: Collection[]): string | null {
  const dates = rows.map((row) => row.received_at).filter((value): value is string => Boolean(value));
  if (dates.length === 0) return null;
  return dates.sort().at(-1) ?? null;
}

function ActionLink({
  children,
  onClick,
  danger = false,
}: {
  children: React.ReactNode;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`text-body font-medium underline-offset-4 hover:underline ${danger ? "text-ember" : "text-ink"}`}
    >
      {children}
    </button>
  );
}

function RowSaveCancel({
  onSave,
  onCancel,
  saveLabel,
  busy = false,
}: {
  onSave: () => void;
  onCancel: () => void;
  saveLabel: string;
  busy?: boolean;
}) {
  return (
    <span className="ui-actions-row relative z-10">
      <button type="button" onClick={onSave} disabled={busy} className="ui-btn ui-btn-primary">
        {busy ? "提交中…" : saveLabel}
      </button>
      <button type="button" onClick={onCancel} disabled={busy} className="ui-btn ui-btn-secondary">
        取消
      </button>
    </span>
  );
}

function ScheduleTableRow({
  item,
  receipts,
  contractId,
  accountKind,
  onChanged,
  onError,
}: {
  item: PaymentSchedule;
  receipts: Collection[];
  contractId: number;
  accountKind: string;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const words = paymentWords(accountKind);
  const [mode, setMode] = useState<"view" | "edit" | "collect">("view");
  const [name, setName] = useState(item.name);
  const [amount, setAmount] = useState(item.amount);
  const [received, setReceived] = useState(leftover(item));
  const [receivedAt, setReceivedAt] = useState(localToday);
  const [busy, setBusy] = useState(false);
  const singleReceipt = receipts.length === 1 ? receipts[0] : null;

  useEffect(() => {
    setName(item.name);
    setAmount(item.amount);
    if (mode === "view") setReceived(leftover(item));
  }, [item.name, item.amount, item.collected_amount, mode]);

  async function savePlan() {
    if (busy) return;
    setBusy(true);
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
      // 只有一笔到账时，编辑也可以改这笔钱和日期，免得登记错了还得整期删掉。
      if (singleReceipt) {
        await api(`/api/v1/contracts/${contractId}/collections/${singleReceipt.id}`, {
          method: "PUT",
          body: JSON.stringify({
            amount: received,
            received_at: receivedAt || null,
            schedule_id: item.id,
            notes: singleReceipt.notes,
          }),
        });
      }
      setMode("view");
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setBusy(false);
    }
  }

  async function confirmReceipt() {
    if (busy) return;
    setBusy(true);
    try {
      await api(`/api/v1/contracts/${contractId}/collections`, {
        method: "POST",
        body: JSON.stringify({
          amount: received,
          received_at: receivedAt || null,
          schedule_id: item.id,
        }),
      });
      setMode("view");
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "登记失败");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    const hasReceipts = receipts.length > 0;
    const message = hasReceipts ? words.deletePlanWithReceipts : words.deletePlan;
    if (!window.confirm(message)) return;
    try {
      for (const receipt of receipts) {
        await api(`/api/v1/contracts/${contractId}/collections/${receipt.id}`, { method: "DELETE" });
      }
      await api(`/api/v1/contracts/${contractId}/schedules/${item.id}`, { method: "DELETE" });
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "删除失败");
    }
  }

  function startCollect() {
    setReceived(leftover(item));
    setReceivedAt(localToday());
    setMode("collect");
  }

  function startEdit() {
    setName(item.name);
    setAmount(item.amount);
    if (singleReceipt) {
      setReceived(singleReceipt.amount);
      setReceivedAt(singleReceipt.received_at ?? "");
    }
    setMode("edit");
  }

  const receivedDate = latestReceivedAt(receipts);
  const onEnter =
    mode === "edit" ? savePlan : mode === "collect" ? confirmReceipt : undefined;

  function handleEnter(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && onEnter) {
      event.preventDefault();
      onEnter();
    }
  }

  return (
    <tr>
      <td>
        {mode === "edit" ? (
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={handleEnter}
            className="ui-input w-36"
            required
          />
        ) : (
          <span className="font-medium">
            {item.period_no}. {item.name}
          </span>
        )}
      </td>
      <td className="ui-money">
        {mode === "edit" ? (
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            onKeyDown={handleEnter}
            className="ui-input w-32"
            required
          />
        ) : (
          money(item.amount)
        )}
      </td>
      <td className="ui-money">
        {mode === "collect" || (mode === "edit" && singleReceipt) ? (
          <input
            type="number"
            step="0.01"
            min="0"
            value={received}
            onChange={(e) => setReceived(e.target.value)}
            onKeyDown={handleEnter}
            className="ui-input w-32"
            required
          />
        ) : (
          money(item.collected_amount)
        )}
      </td>
      <td>
        {mode === "collect" || (mode === "edit" && singleReceipt) ? (
          <input
            type="date"
            value={receivedAt}
            onChange={(e) => setReceivedAt(e.target.value)}
            onKeyDown={handleEnter}
            className="ui-input w-40"
          />
        ) : (
          receivedDate || "—"
        )}
      </td>
      <td className="ui-actions">
        {mode === "edit" ? (
          <RowSaveCancel onSave={savePlan} onCancel={() => setMode("view")} saveLabel="保存" busy={busy} />
        ) : mode === "collect" ? (
          <RowSaveCancel onSave={confirmReceipt} onCancel={() => setMode("view")} saveLabel="确认" busy={busy} />
        ) : (
          <span className="ui-actions-row relative z-10">
            <ActionLink onClick={startEdit}>编辑</ActionLink>
            <ActionLink danger onClick={remove}>
              删除
            </ActionLink>
            <ActionLink onClick={startCollect}>{words.confirm}</ActionLink>
          </span>
        )}
      </td>
    </tr>
  );
}

function LooseCollectionRow({
  item,
  contractId,
  accountKind,
  onChanged,
  onError,
}: {
  item: Collection;
  contractId: number;
  accountKind: string;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState(item.amount);
  const [receivedAt, setReceivedAt] = useState(item.received_at ?? "");

  useEffect(() => {
    setAmount(item.amount);
    setReceivedAt(item.received_at ?? "");
  }, [item.amount, item.received_at]);

  async function save() {
    try {
      await api(`/api/v1/contracts/${contractId}/collections/${item.id}`, {
        method: "PUT",
        body: JSON.stringify({
          amount,
          received_at: receivedAt || null,
          schedule_id: null,
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
    if (!window.confirm(paymentWords(accountKind).deleteReceipt)) return;
    try {
      await api(`/api/v1/contracts/${contractId}/collections/${item.id}`, { method: "DELETE" });
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <tr>
      <td>
        <span className="font-medium">未指定期次</span>
      </td>
      <td>—</td>
      <td className="ui-money">
        {editing ? (
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="ui-input w-32"
            required
          />
        ) : (
          money(item.amount)
        )}
      </td>
      <td>
        {editing ? (
          <input type="date" value={receivedAt} onChange={(e) => setReceivedAt(e.target.value)} className="ui-input w-40" />
        ) : (
          item.received_at || "—"
        )}
      </td>
      <td className="ui-actions">
        {editing ? (
          <RowSaveCancel onSave={save} onCancel={() => setEditing(false)} saveLabel="保存" />
        ) : (
          <span className="ui-actions-row">
            <ActionLink onClick={() => setEditing(true)}>编辑</ActionLink>
            <ActionLink danger onClick={remove}>
              删除
            </ActionLink>
          </span>
        )}
      </td>
    </tr>
  );
}

function PaymentsPanel({
  contractId,
  accountKind,
  schedules,
  collections,
  onChanged,
}: {
  contractId: number;
  accountKind: string;
  schedules: PaymentSchedule[];
  collections: Collection[];
  onChanged: () => Promise<void>;
}) {
  const words = paymentWords(accountKind);
  const [name, setName] = useState(() => nextPeriodName(schedules.length));
  const [amount, setAmount] = useState("0");
  const [error, setError] = useState("");
  const looseCollections = collections.filter((item) => item.schedule_id == null);
  const empty = schedules.length === 0 && looseCollections.length === 0;

  async function addSchedule(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api(`/api/v1/contracts/${contractId}/schedules`, {
        method: "POST",
        body: JSON.stringify({ name, amount }),
      });
      setName(nextPeriodName(schedules.length + 1));
      setAmount("0");
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "添加失败");
    }
  }

  return (
    <div className="space-y-6">
      {error ? <FormError message={error} /> : null}
      <p className="text-body text-mid-gray">{words.hint}</p>
      <PinnedTable pinLeft={1} pinRight={1}>
        <thead>
          <tr>
            <th>期次</th>
            <th className="ui-money">计划金额</th>
            <th className="ui-money">{words.settled}</th>
            <th>{words.date}</th>
            <th className="ui-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          {empty ? (
            <tr>
              <td colSpan={5}>
                <EmptyHint>{words.empty}</EmptyHint>
              </td>
            </tr>
          ) : (
            <>
              {schedules.map((item) => (
                <ScheduleTableRow
                  key={item.id}
                  item={item}
                  receipts={collections.filter((row) => row.schedule_id === item.id)}
                  contractId={contractId}
                  accountKind={accountKind}
                  onChanged={onChanged}
                  onError={setError}
                />
              ))}
              {looseCollections.map((item) => (
                <LooseCollectionRow
                  key={`loose-${item.id}`}
                  item={item}
                  contractId={contractId}
                  accountKind={accountKind}
                  onChanged={onChanged}
                  onError={setError}
                />
              ))}
            </>
          )}
        </tbody>
      </PinnedTable>

      <form onSubmit={addSchedule} className="ui-card flex flex-wrap items-end gap-3 p-6">
        <Field label="期次名称">
          <input value={name} onChange={(e) => setName(e.target.value)} className="ui-input w-36" required />
        </Field>
        <Field label="计划金额（元）">
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="ui-input w-36"
            required
          />
        </Field>
        <button type="submit" className="ui-btn ui-btn-secondary">
          {words.addPlan}
        </button>
      </form>
    </div>
  );
}
