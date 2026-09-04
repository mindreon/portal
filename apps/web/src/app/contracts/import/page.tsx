"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { FormError, PageHeader } from "@/components/ui";
import { uploadFiles } from "@/lib/api";
import type { ImportBatch } from "@/lib/types";

export default function ContractImportPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<ImportBatch | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
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

  return (
    <AppShell>
      <PageHeader eyebrow="Contracts" title="上传解析" />
      <p className="-mt-3 mb-5 max-w-2xl text-body text-mid-gray">
        可一次丢多个 PDF 或一个 zip。有合同编号的合成一份；没有编号的每个文件先单独成草稿，系统用内部
        ID 区分，编号以后再补。扫描件会尝试 OCR，结果都要人核对。
      </p>

      <form onSubmit={onSubmit} className="ui-card max-w-2xl space-y-4 p-5">
        <FormError message={error} />
        <label className="block text-body">
          <span className="mb-1.5 block font-medium text-ink">PDF / zip</span>
          <input
            type="file"
            accept=".pdf,.zip,application/pdf,application/zip"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            className="ui-input"
          />
        </label>
        {files.length > 0 ? (
          <p className="text-body text-mid-gray">已选 {files.length} 个文件</p>
        ) : null}
        <button type="submit" disabled={busy} className="ui-btn ui-btn-primary">
          {busy ? "正在解析…" : "开始解析"}
        </button>
      </form>

      {result ? (
        <section className="mt-8 space-y-3">
          <h3 className="heading-sm">识别结果</h3>
          {result.warning_text ? <p className="text-body text-mid-gray">{result.warning_text}</p> : null}
          {result.contracts.map((item) => (
            <Link key={item.id} href={`/contracts/${item.id}`} className="ui-card block p-5">
              <p className="eyebrow">{item.contract_no ?? "未编号"}</p>
              <p className="mt-1 font-medium text-ink">{item.title}</p>
              <p className="mt-1 text-body text-mid-gray">
                {item.party_a || "甲方待填"} · {item.party_b || "乙方待填"}
              </p>
              <p className="mt-3 text-body font-medium text-ink">去核对 →</p>
            </Link>
          ))}
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => router.push("/contracts")}>
            返回全部合同
          </button>
        </section>
      ) : null}
    </AppShell>
  );
}
