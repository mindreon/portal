export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type ApiOptions = RequestInit & {
  skipAuthRedirect?: boolean;
};

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { skipAuthRedirect, headers, ...rest } = options;
  const response = await fetch(path, {
    credentials: "include",
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });

  if (response.status === 401 && !skipAuthRedirect) {
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "未登录");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : "请求失败";
    throw new ApiError(response.status, message);
  }

  return data as T;
}

export async function uploadFiles<T>(path: string, files: File[]): Promise<T> {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  const response = await fetch(path, { method: "POST", credentials: "include", body });
  if (response.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "未登录");
  }
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : "上传失败";
    throw new ApiError(response.status, message);
  }
  return data as T;
}

export function money(value: string | number, currency = "CNY"): string {
  const amount = Number(value);
  const formatted = Number.isFinite(amount)
    ? amount.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : String(value);
  // 不换行空格：避免「¥」和数字被拆到两行。
  return currency === "CNY" ? `¥\u00a0${formatted}` : `${currency}\u00a0${formatted}`;
}

/** 拼查询字符串。空值会跳过，避免发出 `q=` 这种无意义参数。 */
export function withQuery(
  path: string,
  params: Record<string, string | number | boolean | null | undefined> = {},
): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "" || value === false) continue;
    qs.set(key, String(value));
  }
  const suffix = qs.toString();
  return suffix ? `${path}?${suffix}` : path;
}
