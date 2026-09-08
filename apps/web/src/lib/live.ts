"use client";

import { useEffect, useRef } from "react";

type ImportEvent = {
  type?: string;
  batch_id?: number;
  contract_id?: number | null;
};

/**
 * 听后端 SSE。识别进度一变就回调，用来替换 setInterval 轮询。
 * 只在需要刷新的页面打开连接；离开页面会关掉。
 */
export function useImportLive(enabled: boolean, onUpdate: () => void) {
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  useEffect(() => {
    if (!enabled) return;

    const source = new EventSource("/api/v1/events");

    function handleMessage(event: MessageEvent<string>) {
      if (!event.data) return;
      try {
        const payload = JSON.parse(event.data) as ImportEvent;
        if (payload.type && payload.type !== "import_updated") return;
      } catch {
        return;
      }
      onUpdateRef.current();
    }

    function handleOpen() {
      // 连上后再拉一次，避免「刚提交、连接还没建好」中间漏掉的那条。
      onUpdateRef.current();
    }

    source.addEventListener("open", handleOpen);
    source.addEventListener("message", handleMessage);

    return () => {
      source.removeEventListener("open", handleOpen);
      source.removeEventListener("message", handleMessage);
      source.close();
    };
  }, [enabled]);
}
