"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { PdfPreviewModal, invoiceDownloadUrl, invoicePreviewUrl } from "@/components/pdf-preview";
import { PinnedTable } from "@/components/pinned-table";
import { EmptyHint } from "@/components/ui";
import { api, money, uploadFiles } from "@/lib/api";
import type { Invoice, InvoiceUploadResult } from "@/lib/types";

const MAX_FILE_MB = 200;
const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024;

function onlyPdfs(files: File[]) {
  return files.filter((file) => file.name.toLowerCase().endsWith(".pdf"));
}

export async function uploadInvoicePdfs(files: File[], contractId?: number) {
  const pdfs = onlyPdfs(files);
  if (pdfs.length === 0) {
    throw new Error("请选择 PDF 发票");
  }
  const oversized = pdfs.find((file) => file.size > MAX_FILE_BYTES);
  if (oversized) {
    throw new Error(`${oversized.name} 超过 ${MAX_FILE_MB}MB`);
  }
  return uploadFiles<InvoiceUploadResult>(
    "/api/v1/invoices/upload",
    pdfs,
    contractId ? { contract_id: String(contractId) } : {},
  );
}

export function UploadInvoiceButton({
  contractId,
  onUploaded,
  onError,
  label = "上传发票",
}: {
  contractId?: number;
  onUploaded: (result: InvoiceUploadResult) => Promise<void> | void;
  onError: (message: string) => void;
  label?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  async function onPick(fileList: FileList | null) {
    const files = Array.from(fileList ?? []);
    if (files.length === 0) return;
    setBusy(true);
    try {
      const result = await uploadInvoicePdfs(files, contractId);
      await onUploaded(result);
    } catch (err) {
      onError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        hidden
        onChange={(event) => onPick(event.target.files)}
      />
      <button
        type="button"
        disabled={busy}
        className="ui-btn ui-btn-primary"
        onClick={() => inputRef.current?.click()}
      >
        {busy ? "正在上传…" : label}
      </button>
    </>
  );
}

export function InvoicesPanel({
  contractId,
  invoices,
  onChanged,
  onError,
  onNotice,
}: {
  contractId: number;
  invoices: Invoice[];
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
  onNotice?: (message: string) => void;
}) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<Invoice | null>(null);

  async function handleFiles(fileList: FileList | File[]) {
    const files = Array.from(fileList);
    if (files.length === 0) return;
    setBusy(true);
    try {
      const result = await uploadInvoicePdfs(files, contractId);
      onNotice?.(result.warning_text || "");
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setBusy(false);
    }
  }

  async function remove(item: Invoice) {
    const name = item.original_name || item.title;
    if (!window.confirm(`确定删除发票「${name}」？PDF 也会一起删掉。`)) return;
    try {
      await api(`/api/v1/invoices/${item.id}`, { method: "DELETE" });
      if (preview?.id === item.id) setPreview(null);
      onNotice?.("");
      await onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <div className="space-y-4">
      <label
        className={`drop-zone ${dragging ? "drop-zone-active" : ""}`}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
      >
        <input
          type="file"
          accept="application/pdf,.pdf"
          multiple
          className="sr-only"
          disabled={busy}
          onChange={(event) => {
            handleFiles(event.target.files ?? []);
            event.target.value = "";
          }}
        />
        <p className="font-medium text-ink">{busy ? "正在上传…" : "把发票 PDF 拖到这里，或点这里选择文件"}</p>
        <p className="mt-2 text-body text-mid-gray">
          可以一次选多张。每张 PDF 会变成一行发票，号码可以稍后在编辑里补。单个文件不超过 {MAX_FILE_MB}MB。
        </p>
      </label>

      <PinnedTable pinLeft={1} pinRight={1}>
        <thead>
          <tr>
            <th>发票</th>
            <th>代码 / 号码</th>
            <th className="ui-money">金额</th>
            <th className="ui-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          {invoices.length === 0 ? (
            <tr>
              <td colSpan={4}>
                <EmptyHint>还没有发票。把 PDF 拖到上方，或点右上角上传。</EmptyHint>
              </td>
            </tr>
          ) : (
            invoices.map((item) => (
              <tr key={item.id}>
                <td>
                  <button
                    type="button"
                    className="text-left font-medium hover:underline"
                    onClick={() => (item.has_file ? setPreview(item) : undefined)}
                    disabled={!item.has_file}
                  >
                    {item.title}
                  </button>
                  {item.original_name ? (
                    <p className="mt-1 text-[12px] text-mid-gray">{item.original_name}</p>
                  ) : null}
                </td>
                <td>
                  {item.invoice_code || "—"} / {item.invoice_no.startsWith("UP-") ? "待填写" : item.invoice_no}
                </td>
                <td className="ui-money">{money(item.amount, item.currency)}</td>
                <td className="ui-actions">
                  <span className="ui-actions-row relative z-10">
                    {item.has_file ? (
                      <button
                        type="button"
                        className="text-body font-medium underline-offset-4 hover:underline"
                        onClick={() => setPreview(item)}
                      >
                        预览
                      </button>
                    ) : null}
                    <Link href={`/invoices/${item.id}`} className="text-body font-medium underline-offset-4 hover:underline">
                      编辑
                    </Link>
                    <button
                      type="button"
                      className="text-body font-medium text-ember underline-offset-4 hover:underline"
                      onClick={() => remove(item)}
                    >
                      删除
                    </button>
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </PinnedTable>

      <PdfPreviewModal
        open={preview != null && preview.has_file}
        title={preview?.original_name || preview?.title || "发票"}
        src={preview ? invoicePreviewUrl(preview.id) : ""}
        downloadHref={preview ? invoiceDownloadUrl(preview.id) : undefined}
        onClose={() => setPreview(null)}
      />
    </div>
  );
}
