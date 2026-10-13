import { NextRequest, NextResponse } from "next/server";

const TARGET_HOST = (process.env.BACKEND_PROXY_URL || "https://salep-staging.icdigital.io").replace(/\/$/, "");

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const targetUrl = new URL(
    `/api/${path.join("/")}${request.nextUrl.search}`,
    TARGET_HOST
  );

  const headers = new Headers(request.headers);
  const targetOrigin = new URL(TARGET_HOST);
  headers.set("host", targetOrigin.host);
  headers.set("origin", targetOrigin.origin);
  headers.set("referer", `${targetOrigin.origin}/`);
  headers.set("sec-fetch-site", "same-origin");

  const body = ["GET", "HEAD"].includes(request.method)
    ? undefined
    : await request.arrayBuffer();

  let response = await fetch(targetUrl.toString(), {
    method: request.method,
    headers,
    body,
    redirect: "manual",
  });

  // Fallback staging: backend staging versi lama melempar 500 bila query fiscal_years dikirim
  // karena bug validasi list ge/le di Pydantic. Jika terjadi 500, coba ulang tanpa param fiscal_years.
  if (
    response.status === 500 &&
    targetUrl.pathname.includes("/inaproc/final") &&
    targetUrl.searchParams.has("fiscal_years")
  ) {
    const fallbackUrl = new URL(targetUrl.toString());
    fallbackUrl.searchParams.delete("fiscal_years");
    response = await fetch(fallbackUrl.toString(), {
      method: request.method,
      headers,
      body,
      redirect: "manual",
    });
  }

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  responseHeaders.delete("set-cookie");

  const res = new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });

  if (typeof response.headers.getSetCookie === "function") {
    for (const cookie of response.headers.getSetCookie()) {
      let localCookie = cookie;
      if (request.nextUrl.protocol === "http:") {
        // Hilangkan flag Secure dan longgarkan SameSite ke Lax agar cookie sesi aman disimpan di http://localhost
        localCookie = localCookie
          .replace(/;\s*Secure/gi, "")
          .replace(/;\s*SameSite=Strict/gi, "; SameSite=Lax");
      }
      res.headers.append("set-cookie", localCookie);
    }
  }

  return res;
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
