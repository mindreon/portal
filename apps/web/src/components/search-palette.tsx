"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { api } from "@/lib/api";
import { searchShortcuts } from "@/lib/modules";
import type { Contract, Invoice } from "@/lib/types";

type Hit = { href: string; title: string; meta: string };

function match(query: string, text: string | null | undefined) {
  return (text ?? "").toLowerCase().includes(query.toLowerCase());
}

export function SearchPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => !current);
      }
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    inputRef.current?.focus();
    Promise.all([api<Contract[]>("/api/v1/contracts"), api<Invoice[]>("/api/v1/invoices")])
      .then(([nextContracts, nextInvoices]) => {
        setContracts(nextContracts);
        setInvoices(nextInvoices);
      })
      .catch(() => undefined);
  }, [open]);

  const hits = useMemo(() => {
    const q = query.trim();
    const shortcuts = searchShortcuts();
    const pages = q ? shortcuts.filter((item) => match(q, item.title) || match(q, item.meta)) : shortcuts;
    const contractHits = contracts
      .filter((item) => !q || match(q, item.title) || match(q, item.contract_no) || match(q, item.counterparty))
      .slice(0, 6)
      .map((item) => ({
        href: `/contracts/${item.id}`,
        title: item.title,
        meta: `合同 · ${item.contract_no}`,
      }));
    const invoiceHits = invoices
      .filter((item) => !q || match(q, item.title) || match(q, item.invoice_no) || match(q, item.counterparty))
      .slice(0, 6)
      .map((item) => ({
        href: `/invoices/${item.id}`,
        title: item.title,
        meta: `发票 · ${item.invoice_no}`,
      }));
    return [...pages, ...contractHits, ...invoiceHits];
  }, [query, contracts, invoices]);

  function go(href: string) {
    setOpen(false);
    router.push(href);
  }

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="search-trigger">
        <span>搜索模块或记录…</span>
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
            <ul className="mt-3 max-h-80 overflow-auto">
              {hits.length === 0 ? (
                <li className="px-2 py-3 text-body text-mid-gray">没有匹配项</li>
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
