import { NextRequest, NextResponse } from "next/server";

const TARGET_HOST = "https://salep-staging.icdigital.io";

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
  headers.set("host", "salep-staging.icdigital.io");
  headers.set("origin", TARGET_HOST);
  headers.set("referer", `${TARGET_HOST}/`);
  headers.set("sec-fetch-site", "same-origin");

  const body = ["GET", "HEAD"].includes(request.method)
    ? undefined
    : await request.arrayBuffer();

  const response = await fetch(targetUrl.toString(), {
    method: request.method,
    headers,
    body,
    redirect: "manual",
  });

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
