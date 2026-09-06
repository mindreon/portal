"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { ContractEditor } from "../contract-editor";
import { AppShell } from "@/components/app-shell";
import { FormError, PageHeader } from "@/components/ui";
import { uploadFiles } from "@/lib/api";
import type { ImportBatch } from "@/lib/types";

function NewContractForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<"upload" | "manual">(
    searchParams.get("mode") === "manual" ? "manual" : "upload",
  );
  const [files, setFiles] = useState<File[]>([]);
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
      // 上传接口只负责收文件、解压落盘、建占位合同；识别在后台跑。
      await uploadFiles<ImportBatch>("/api/v1/contracts/imports", files);
      router.push("/contracts");
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
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
        description="上传 PDF 或 zip 后会立刻出现在合同列表里，识别在后台继续，刷新页面也不会中断。"
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
            {busy ? "正在上传…" : "上传并开始识别"}
          </button>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => setMode("manual")}>
            没有文件，手工填写
          </button>
        </div>
      </form>
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
