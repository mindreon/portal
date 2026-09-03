/** 装饰色块：绿 / 粉 / 黄 / 墨只允许用在登录页背后，不进按钮。 */
export function GardenBlobs() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <span className="garden-blob top-[-80px] left-[-40px] h-72 w-80 bg-moss-green" />
      <span className="garden-blob top-[12%] right-[-60px] h-64 w-72 rotate-12 bg-fuchsia" />
      <span className="garden-blob bottom-[-40px] left-[18%] h-56 w-64 -rotate-6 bg-hi-yellow" />
      <span className="garden-blob right-[22%] bottom-[8%] h-40 w-48 rotate-45 bg-deep-ink opacity-90" />
    </div>
  );
}
