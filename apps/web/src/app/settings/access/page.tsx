"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PinnedTable } from "@/components/pinned-table";
import { EmptyHint, FormError, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { useCurrentUser } from "@/lib/current-user";
import { MODULES } from "@/lib/modules";
import type { ManagedUser } from "@/lib/types";

/**
 * 管理员在这里给每个人勾选模块。
 *
 * 可以想成：飞书只发工牌，这张表才是「这栋楼哪些房间的钥匙」。
 * 同事必须先登录一次，才会出现在名单里。
 */
export default function AccessPage() {
  const { user: me, reload } = useCurrentUser();
  const [rows, setRows] = useState<ManagedUser[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  async function load() {
    const next = await api<ManagedUser[]>("/api/v1/users");
    setRows(next);
  }

  useEffect(() => {
    load().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "无法加载人员列表");
    });
  }, []);

  async function save(userId: number, payload: { role?: string; modules?: string[] }) {
    setBusyId(userId);
    setError("");
    try {
      const next = await api<ManagedUser>(`/api/v1/users/${userId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      setRows((current) => current.map((row) => (row.id === next.id ? next : row)));
      if (me?.id === userId) await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setBusyId(null);
    }
  }

  function toggleModule(row: ManagedUser, moduleId: string, checked: boolean) {
    const next = checked ? [...row.modules, moduleId] : row.modules.filter((item) => item !== moduleId);
    void save(row.id, { modules: MODULES.map((item) => item.id).filter((id) => next.includes(id)) });
  }

  function toggleAdmin(row: ManagedUser, checked: boolean) {
    void save(row.id, { role: checked ? "admin" : "member" });
  }

  return (
    <AppShell>
      <PageHeader
        title="人员权限"
        description="勾选之后立刻生效。同事用飞书登录一次后才会出现在这张表里。至少保留一名管理员，否则没人能再打开这一页。"
      />

      <FormError message={error} />

      <PinnedTable pinLeft={1} minWidth={720}>
        <thead>
          <tr>
            <th>同事</th>
            {MODULES.map((item) => (
              <th key={item.id}>{item.name}</th>
            ))}
            <th>可管理权限</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={MODULES.length + 2}>
                <EmptyHint>还没有其它账号。请同事先用飞书登录一次。</EmptyHint>
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const disabled = busyId === row.id;
              return (
                <tr key={row.id}>
                  <td>
                    <p className="font-medium text-ink">
                      {row.name}
                      {me?.id === row.id ? "（我）" : ""}
                    </p>
                    <p className="mt-1 text-[12px] text-mid-gray">{row.email || "未绑定邮箱"}</p>
                  </td>
                  {MODULES.map((item) => (
                    <td key={item.id}>
                      <label className="ui-check">
                        <input
                          type="checkbox"
                          checked={row.modules.includes(item.id)}
                          disabled={disabled}
                          onChange={(event) => toggleModule(row, item.id, event.target.checked)}
                        />
                        <span className="sr-only">{item.name}</span>
                      </label>
                    </td>
                  ))}
                  <td>
                    <label className="ui-check">
                      <input
                        type="checkbox"
                        checked={row.role === "admin"}
                        disabled={disabled}
                        onChange={(event) => toggleAdmin(row, event.target.checked)}
                      />
                      <span>管理员</span>
                    </label>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </PinnedTable>
    </AppShell>
  );
}
