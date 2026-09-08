"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { api, withQuery } from "@/lib/api";
import { useCurrentUser } from "@/lib/current-user";
import { searchShortcuts } from "@/lib/modules";
import type { Contract, Invoice, PageResult } from "@/lib/types";

function match(query: string, text: string | null | undefined) {
  return (text ?? "").toLowerCase().includes(query.toLowerCase());
}

export function SearchPalette() {
  const router = useRouter();
  const { user, canAccess } = useCurrentUser();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  function openPalette() {
    setQuery("");
    setOpen(true);
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => {
          if (current) return false;
          setQuery("");
          return true;
        });
      }
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const handle = window.setTimeout(async () => {
      const params = { q: query.trim() || undefined, page: 1, page_size: 6 };
      const jobs: Promise<void>[] = [];
      if (canAccess("contracts")) {
        jobs.push(
          api<PageResult<Contract>>(withQuery("/api/v1/contracts", params)).then((page) => setContracts(page.items)),
        );
      } else {
        setContracts([]);
      }
      if (canAccess("invoices")) {
        jobs.push(
          api<PageResult<Invoice>>(withQuery("/api/v1/invoices", params)).then((page) => setInvoices(page.items)),
        );
      } else {
        setInvoices([]);
      }
      await Promise.all(jobs).catch(() => undefined);
    }, query.trim() ? 200 : 0);
    return () => window.clearTimeout(handle);
  }, [open, query, canAccess]);

  const hits = useMemo(() => {
    const q = query.trim();
    const shortcuts = searchShortcuts(user);
    const pages = q ? shortcuts.filter((item) => match(q, item.title) || match(q, item.meta)) : shortcuts;
    const contractHits = contracts.map((item) => ({
      href: `/contracts/${item.id}`,
      title: item.title,
      meta: `合同 · ${item.contract_no || item.id}`,
    }));
    const invoiceHits = invoices.map((item) => ({
      href: `/invoices/${item.id}`,
      title: item.title,
      meta: `发票 · ${item.invoice_no}`,
    }));
    return [...pages, ...contractHits, ...invoiceHits];
  }, [query, contracts, invoices, user]);

  function go(href: string) {
    setOpen(false);
    router.push(href);
  }

  return (
    <>
      <button type="button" onClick={openPalette} className="search-trigger">
        <span className="inline-flex min-w-0 items-center gap-2">
          <Icon name="search" size={16} className="shrink-0 text-mid-gray" />
          <span>搜索模块或记录…</span>
        </span>
        <kbd>⌘K</kbd>
      </button>

      {open ? (
        <div className="search-overlay" onClick={() => setOpen(false)}>
          <div className="ui-card search-panel" onClick={(event) => event.stopPropagation()}>
            <input
              ref={inputRef}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="跳转到模块，或按名称搜索"
              className="ui-input"
            />
            <ul className="mt-4 max-h-80 overflow-auto">
              {hits.length === 0 ? (
                <li className="px-3 py-4 text-body text-mid-gray">没有匹配项</li>
              ) : (
                hits.map((hit) => (
                  <li key={`${hit.href}-${hit.title}`}>
                    <button type="button" onClick={() => go(hit.href)} className="search-hit">
                      <span className="font-medium text-ink">{hit.title}</span>
                      <span className="text-[12px] tracking-[0.6px] text-mid-gray uppercase">{hit.meta}</span>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>
      ) : null}
    </>
  );
}
