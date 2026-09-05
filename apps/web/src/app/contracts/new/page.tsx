"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { ContractEditor } from "../contract-editor";
import { AppShell } from "@/components/app-shell";
import { FilePreview } from "@/components/file-preview";
import { FormError, PageHeader } from "@/components/ui";
import { uploadFiles } from "@/lib/api";
import type { ImportBatch } from "@/lib/types";

function NewContractForm() {
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<"upload" | "manual">(
    searchParams.get("mode") === "manual" ? "manual" : "upload",
  );
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<ImportBatch | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onUpload(event: React.FormEvent) {
    event.preventDefault();
    if (files.length === 0) {
      setError("请先选择 PDF 或 zip");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const data = await uploadFiles<ImportBatch>("/api/v1/contracts/imports", files);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "解析失败");
    } finally {
      setBusy(false);
    }
  }

  if (mode === "manual") {
    return <ContractEditor onSwitchToUpload={() => setMode("upload")} />;
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Contracts"
        title="新建合同"
        description="优先上传 PDF 或 zip，系统识别后再核对。没有扫描件时再手工填写。"
      />

      <form onSubmit={onUpload} className="ui-card max-w-2xl space-y-5 p-6">
        <FormError message={error} />
        <label className="block text-body">
          <span className="mb-2 block font-medium text-ink">PDF / zip</span>
          <input
            type="file"
            accept=".pdf,.zip,application/pdf,application/zip"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            className="ui-input"
          />
        </label>
        {files.length > 0 ? <p className="text-body text-mid-gray">已选 {files.length} 个文件</p> : null}
        <div className="flex flex-wrap gap-3">
          <button type="submit" disabled={busy} className="ui-btn ui-btn-primary">
            {busy ? "正在解析…" : "开始解析"}
          </button>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => setMode("manual")}>
            没有文件，手工填写
          </button>
        </div>
      </form>

      {result ? (
        <section className="mt-8 space-y-4">
          <h3 className="heading-sm">识别结果</h3>
          {result.warning_text ? (
            <p className="whitespace-pre-wrap text-body text-mid-gray">{result.warning_text}</p>
          ) : null}
          {result.contracts.length === 0 ? (
            <p className="text-body text-mid-gray">没有新建合同。若提示内容相同，说明这份文件已经在库里。</p>
          ) : null}
          {result.contracts.map((item) => (
            <Link key={item.id} href={`/contracts/${item.id}`} className="ui-card block p-6">
              <p className="eyebrow">{item.contract_no ?? "未编号"}</p>
              <p className="mt-2 font-medium text-ink">{item.title}</p>
              <p className="mt-2 text-body text-mid-gray">
                {item.party_a || "甲方待填"} · {item.party_b || "乙方待填"}
              </p>
              <p className="mt-5 text-body font-medium text-ink">去核对 →</p>
            </Link>
          ))}
          {result.files.map((item) => (
            <article key={item.id} className="ui-card p-6">
              <p className="font-medium text-ink">{item.original_name}</p>
              <FilePreview fileId={item.id} name={item.original_name} />
            </article>
          ))}
        </section>
      ) : null}
    </AppShell>
  );
}

export default function NewContractPage() {
  return (
    <Suspense>
      <NewContractForm />
    </Suspense>
  );
}
