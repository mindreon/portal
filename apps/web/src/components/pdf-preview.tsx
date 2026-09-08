"use client";

import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

const ZOOM_MIN = 0.5;
const ZOOM_MAX = 3;
const ZOOM_STEP = 0.25;

function clampZoom(value: number) {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(value * 100) / 100));
}

function formatZoom(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function invoicePreviewUrl(invoiceId: number) {
  return `/api/v1/invoices/${invoiceId}/preview`;
}

export function invoiceDownloadUrl(invoiceId: number) {
  return `/api/v1/invoices/${invoiceId}/download`;
}

export function PdfZoomStage({
  title,
  src,
  downloadHref,
  extra,
  compact = false,
}: {
  title: string;
  src: string;
  downloadHref?: string;
  extra?: ReactNode;
  compact?: boolean;
}) {
  const [zoom, setZoom] = useState(1);
  const stageRef = useRef<HTMLDivElement>(null);

  function zoomBy(delta: number) {
    setZoom((current) => clampZoom(current + delta));
  }

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    function onWheel(event: WheelEvent) {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      setZoom((current) => clampZoom(current + (event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP)));
    }
    stage.addEventListener("wheel", onWheel, { passive: false });
    return () => stage.removeEventListener("wheel", onWheel);
  }, []);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable)
      ) {
        return;
      }
      if (event.key === "+" || event.key === "=") {
        event.preventDefault();
        zoomBy(ZOOM_STEP);
      }
      if (event.key === "-" || event.key === "_") {
        event.preventDefault();
        zoomBy(-ZOOM_STEP);
      }
      if (event.key === "0") {
        setZoom(1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const frameStyle = { zoom } as CSSProperties;

  return (
    <div className="preview-stage-wrap">
      <div className="preview-toolbar">
        <p className="min-w-0 truncate font-medium text-ink">{title}</p>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => zoomBy(-ZOOM_STEP)}>
            缩小
          </button>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => setZoom(1)} title="回到 100%">
            {formatZoom(zoom)}
          </button>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => zoomBy(ZOOM_STEP)}>
            放大
          </button>
          {downloadHref ? (
            <a href={downloadHref} className="ui-btn ui-btn-secondary">
              下载
            </a>
          ) : null}
          {extra}
        </div>
      </div>
      <div
        ref={stageRef}
        className={compact ? "preview-stage preview-stage-compact" : "preview-stage"}
      >
        <iframe title={title} src={src} className="preview-frame" style={frameStyle} />
      </div>
      <p className="preview-hint">可以用缩小 / 放大，或 Ctrl + 滚轮。按 0 回到 100%，按 Esc 关闭预览。</p>
    </div>
  );
}

export function PdfPreviewModal({
  open,
  title,
  src,
  downloadHref,
  onClose,
}: {
  open: boolean;
  title: string;
  src: string;
  downloadHref?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="preview-overlay" role="dialog" aria-modal="true" aria-label={title}>
      <button type="button" className="preview-backdrop" aria-label="关闭预览" onClick={onClose} />
      <div className="preview-shell ui-card">
        <PdfZoomStage
          title={title}
          src={src}
          downloadHref={downloadHref}
          extra={
            <button type="button" className="ui-btn ui-btn-secondary" onClick={onClose}>
              关闭
            </button>
          }
        />
      </div>
    </div>
  );
}
