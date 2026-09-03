"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { FormError } from "@/components/ui";
import { api } from "@/lib/api";
import type { AuthConfig } from "@/lib/types";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [name, setName] = useState("本地管理员");
  const [error, setError] = useState(searchParams.get("error") ?? "");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<AuthConfig>("/api/v1/auth/config", { skipAuthRedirect: true }).then(setConfig);
  }, []);

  async function loginFeishu() {
    setBusy(true);
    setError("");
    try {
      const data = await api<{ authorize_url: string }>("/api/v1/auth/feishu/login", {
        skipAuthRedirect: true,
      });
      window.location.href = data.authorize_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法开始飞书登录");
      setBusy(false);
    }
  }

  async function loginDev(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/api/v1/auth/dev-login", {
        method: "POST",
        body: JSON.stringify({ name }),
        skipAuthRedirect: true,
      });
      router.replace("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "开发登录失败");
      setBusy(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4">
      <div className="ui-card w-full max-w-md rounded-[28px] p-8">
        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[var(--mint)] text-base font-black text-[#06241b] shadow-[0_0_24px_var(--glow-mint)]">
            P
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-[var(--muted)]">AI Lab · Internal</p>
            <h1 className="text-2xl font-semibold">欢迎回来</h1>
          </div>
        </div>
        <p className="text-sm leading-6 text-[var(--muted)]">
          正式环境用飞书进团队空间。合同和发票是两套独立模块，登录后各走各的页面。
        </p>

        <div className="mt-5">
          <FormError message={error} />
        </div>

        <div className="mt-6 space-y-4">
          {config?.feishu_enabled ? (
            <button type="button" onClick={loginFeishu} disabled={busy} className="ui-btn ui-btn-indigo w-full">
              使用飞书登录
            </button>
          ) : (
            <p className="rounded-2xl bg-white/5 px-3 py-2 text-sm text-[var(--muted)]">
              还没填写 <code className="text-[var(--mint)]">FEISHU_APP_ID</code>
              。配好飞书后，这里会亮起登录按钮。
            </p>
          )}

          {config?.dev_login_enabled ? (
            <form onSubmit={loginDev} className="space-y-3 border-t border-[var(--line)] pt-4">
              <label className="block text-sm text-[var(--muted)]">
                开发登录显示名
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  className="ui-input mt-1.5"
                />
              </label>
              <button type="submit" disabled={busy} className="ui-btn ui-btn-mint w-full">
                开发环境登录
              </button>
            </form>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
