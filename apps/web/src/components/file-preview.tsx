"use client";

function fileKind(name: string): "pdf" | "image" | "other" {
  const lower = name.toLowerCase();
  if (lower.endsWith(".pdf")) return "pdf";
  if (/\.(png|jpe?g|gif|webp|bmp)$/i.test(lower)) return "image";
  return "other";
}

export function filePreviewUrl(fileId: number) {
  return `/api/v1/contracts/imports/files/${fileId}/preview`;
}

export function fileDownloadUrl(fileId: number) {
  return `/api/v1/contracts/imports/files/${fileId}/download`;
}

export function FileActions({ fileId }: { fileId: number }) {
  const previewUrl = filePreviewUrl(fileId);
  const downloadUrl = fileDownloadUrl(fileId);

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-4">
      <a href={previewUrl} target="_blank" rel="noreferrer" className="text-body font-medium underline-offset-4 hover:underline">
        新窗口预览
      </a>
      <a href={downloadUrl} className="text-body font-medium underline-offset-4 hover:underline">
        下载原件
      </a>
    </div>
  );
}

export function FilePreview({ fileId, name }: { fileId: number; name: string }) {
  const kind = fileKind(name);
  const previewUrl = filePreviewUrl(fileId);

  if (kind === "other") {
    return null;
  }

  return (
    <div className="mt-4">
      {kind === "pdf" ? (
        <iframe
          title={name}
          src={previewUrl}
          className="h-[640px] w-full rounded-[18px] border border-hairline bg-paper"
        />
      ) : null}
      {kind === "image" ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          alt={name}
          src={previewUrl}
          className="max-h-[640px] w-full rounded-[18px] border border-hairline bg-paper object-contain"
        />
      ) : null}
    </div>
  );
}
