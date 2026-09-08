import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const apiUrl = process.env.API_INTERNAL_URL || "http://localhost:8000";

/**
 * 开发时 Next 会把 /api 转发给 FastAPI，但默认 rewrite 可能把 SSE 攒在缓冲区里。
 * 这条路由单独把事件流原样转出去。生产环境 Caddy 直接打到 FastAPI，不会走到这里。
 */
export async function GET(request: NextRequest) {
  const upstream = await fetch(`${apiUrl}/api/v1/events`, {
    headers: {
      cookie: request.headers.get("cookie") ?? "",
      accept: "text/event-stream",
    },
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
