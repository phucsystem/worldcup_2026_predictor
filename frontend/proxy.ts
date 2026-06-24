// Next 16 Proxy (formerly "middleware") — gates the admin area. Runs on the
// Node.js runtime, so node:crypto in admin-auth works directly. Re-verified in
// each admin route handler (defence-in-depth); this is the redirect gate.
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/admin-auth";

export const config = { matcher: ["/admin/:path*"] };

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // The login page must stay reachable while unauthenticated.
  if (pathname === "/admin/login") return NextResponse.next();

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (verifySessionToken(token, Date.now())) return NextResponse.next();

  const url = request.nextUrl.clone();
  url.pathname = "/admin/login";
  url.search = "";
  return NextResponse.redirect(url);
}
