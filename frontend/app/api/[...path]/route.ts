import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path.some(p => !p || p === "." || p === ".." || /[\\/]/.test(p)) || request.nextUrl.search.length > 2048) {
    return Response.json({detail: "Invalid research request"}, {status: 400});
  }
  const base = process.env.API_INTERNAL_URL || (process.env.NODE_ENV !== "production" ? "http://127.0.0.1:8000" : "");
  try {
    const url = new URL(base);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== "/") throw Error("invalid configuration");
    if (["localhost", "127.0.0.1", "::1", "[::1]"].includes(url.hostname) && process.env.NODE_ENV === "production" && process.env.NEUROGENE_ALLOW_LOCAL_API !== "1") throw Error("local API is not enabled");
    url.pathname = "/api/" + path.map(encodeURIComponent).join("/");
    url.search = request.nextUrl.search;
    const upstream = await fetch(url, {method: request.method, signal: AbortSignal.timeout(20000), cache: "no-store", redirect: "error", headers: {Accept: request.headers.get("accept") || "application/json"}});
    const headers = new Headers({"Cache-Control": "no-store"});
    for (const key of ["content-type", "content-disposition", "x-scientific-scope", "x-cohort-caution", "x-publication-status", "x-request-id", "retry-after"]) {
      const value = upstream.headers.get(key); if (value) headers.set(key, value);
    }
    return new Response(upstream.body, {status: upstream.status, headers});
  } catch {
    return Response.json({detail: "Research backend unavailable; retry later"}, {status: 503});
  }
}

export const GET = proxy;
export const HEAD = proxy;
