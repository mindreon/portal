"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { LogoMark } from "@/components/logo";
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

  const feishuOn = Boolean(config?.feishu_enabled);
  const devOn = Boolean(config?.dev_login_enabled);

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="ui-card w-full max-w-md p-5">
        <div className="mb-5 flex items-center gap-2">
          <LogoMark />
          <p className="eyebrow">Portal · Internal</p>
        </div>
        <h1 className="heading-display">欢迎回来</h1>
        <p className="mt-3 text-body text-mid-gray">
          正式环境用飞书进入。合同和发票是两套独立模块，登录后各走各的页面。
        </p>

        <div className="mt-4">
          <FormError message={error} />
        </div>

        <div className="mt-6 space-y-3">
          {feishuOn ? (
            <button type="button" onClick={loginFeishu} disabled={busy} className="ui-btn ui-btn-primary w-full">
              使用飞书登录
            </button>
          ) : (
            <p className="text-body text-mid-gray">
              还没填写 <code className="font-medium text-ink">FEISHU_APP_ID</code>
              。配好飞书后，这里会出现主登录按钮。
            </p>
          )}

          {devOn ? (
            <form onSubmit={loginDev} className="space-y-3">
              <label className="block text-body text-mid-gray">
                开发登录显示名
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  className="ui-input mt-1.5"
                />
              </label>
              <button
                type="submit"
                disabled={busy}
                className={`ui-btn w-full ${feishuOn ? "ui-btn-secondary" : "ui-btn-primary"}`}
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
