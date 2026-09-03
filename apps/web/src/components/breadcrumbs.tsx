"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Crumb = { href?: string; label: string };

function crumbsFor(pathname: string): Crumb[] {
  if (pathname === "/") return [{ label: "总览" }];
  if (pathname === "/contracts") return [{ href: "/", label: "总览" }, { label: "合同" }];
  if (pathname === "/contracts/new") {
    return [{ href: "/", label: "总览" }, { href: "/contracts", label: "合同" }, { label: "新建" }];
  }
  if (pathname.startsWith("/contracts/")) {
    return [{ href: "/", label: "总览" }, { href: "/contracts", label: "合同" }, { label: "编辑" }];
  }
  if (pathname === "/invoices") return [{ href: "/", label: "总览" }, { label: "发票" }];
  if (pathname === "/invoices/new") {
    return [{ href: "/", label: "总览" }, { href: "/invoices", label: "发票" }, { label: "新建" }];
  }
  if (pathname.startsWith("/invoices/")) {
    return [{ href: "/", label: "总览" }, { href: "/invoices", label: "发票" }, { label: "编辑" }];
  }
  return [{ label: "总览" }];
}

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true" className="text-mid-gray">
      <path d="M4.2 2.4 7.8 6 4.2 9.6" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const crumbs = crumbsFor(pathname);

  return (
    <nav aria-label="面包屑" className="flex flex-wrap items-center gap-1.5 text-body">
      {crumbs.map((crumb, index) => {
        const last = index === crumbs.length - 1;
        return (
          <span key={`${crumb.label}-${index}`} className="flex items-center gap-1.5">
            {index > 0 ? <Chevron /> : null}
            {crumb.href && !last ? (
              <Link href={crumb.href} className="text-mid-gray hover:text-ink">
                {crumb.label}
              </Link>
            ) : (
              <span className="text-ink">{crumb.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
