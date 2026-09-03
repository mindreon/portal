export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" aria-hidden="true">
      <path
        fill="#130e30"
        d="M18 2c4.8 0 7.4 3.6 8.6 6.4 1.8 4.2 1.2 9.2-1.4 12.8-2.4 3.4-6.2 6.4-9.8 8.2-2.2-3.6-5.8-6.6-6.8-11.2C7.2 12.4 10.6 2 18 2Z"
      />
      <path
        fill="#f9fbf2"
        d="M17.2 8.2c2.4.2 4.2 2.4 4 4.8-.2 2.2-2 3.8-3.8 4.6 0-1.8-.6-4.2-2.4-5.6 0-1.8.6-3.6 2.2-3.8Z"
      />
    </svg>
  );
}

export function LogoLockup() {
  return (
    <div className="flex items-center gap-3">
      <LogoMark />
      <div>
        <p className="eyebrow">Internal</p>
        <p className="font-hedvig text-[22px] font-bold leading-[1.25] tracking-[-0.22px]">Portal</p>
      </div>
    </div>
  );
}
