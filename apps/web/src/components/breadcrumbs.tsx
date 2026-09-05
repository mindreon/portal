"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { crumbsFor } from "@/lib/modules";

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
    <nav aria-label="面包屑" className="flex flex-wrap items-center gap-2 text-body">
      {crumbs.map((crumb, index) => {
        const last = index === crumbs.length - 1;
        return (
          <span key={`${crumb.label}-${index}`} className="flex items-center gap-2">
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
