"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

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
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl border border-[var(--line)] bg-[var(--card)] p-8 shadow-sm">
        <p className="text-xs tracking-[0.24em] uppercase text-[#8a6a3b]">公司内部</p>
        <h1 className="mt-2 text-3xl font-semibold">登录 Portal</h1>
        <p className="mt-2 text-sm leading-6 text-[#6f6253]">
          正式环境用飞书企业账号进入。本地还没配飞书时，可以用开发登录先把合同和发票跑通。
        </p>

        {error ? (
          <p className="mt-4 rounded-md bg-[#f8e8e4] px-3 py-2 text-sm text-[#8a3030]">{error}</p>
        ) : null}

        <div className="mt-6 space-y-4">
          {config?.feishu_enabled ? (
            <button
              type="button"
              onClick={loginFeishu}
              disabled={busy}
              className="w-full rounded-lg bg-[#3370ff] px-4 py-3 text-white hover:bg-[#2b62e0] disabled:opacity-60"
            >
              使用飞书登录
            </button>
          ) : (
            <p className="rounded-md bg-[#eef2f7] px-3 py-2 text-sm text-[#3d5066]">
              还没填写 <code>FEISHU_APP_ID</code>。配好飞书应用后，这里会出现飞书登录按钮。
            </p>
          )}

          {config?.dev_login_enabled ? (
            <form onSubmit={loginDev} className="space-y-3 border-t border-[var(--line)] pt-4">
              <label className="block text-sm">
                开发登录显示名
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  className="mt-1 w-full rounded-md border border-[var(--line)] bg-white px-3 py-2"
                />
              </label>
              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-[var(--navy)] px-4 py-3 text-white hover:bg-[#11263d] disabled:opacity-60"
              >
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
