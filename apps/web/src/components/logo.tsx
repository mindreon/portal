export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" aria-hidden="true">
      <rect width="28" height="28" rx="8" fill="#0a0a0a" />
      <path d="M8 18.5V9.5h4.2c2.4 0 3.8 1.3 3.8 3.3 0 2.1-1.5 3.4-3.9 3.4H10.4V18.5H8Zm2.4-4.2h1.6c1.1 0 1.7-.5 1.7-1.4s-.6-1.4-1.7-1.4H10.4v2.8Z" fill="#fafafa" />
    </svg>
  );
}

export function LogoLockup() {
  return (
    <div className="flex items-center gap-3">
      <LogoMark />
      <div>
        <p className="eyebrow">Internal</p>
        <p className="text-[16px] font-semibold tracking-[-0.4px] text-ink">Portal</p>
      </div>
    </div>
  );
}
