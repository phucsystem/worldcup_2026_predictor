// Server-only single-admin session. Imported by proxy.ts, admin route handlers,
// and admin server components — NEVER by a client component (it reads the
// password/secret from env and uses node:crypto, which also prevents bundling).
import crypto from "node:crypto";

export const SESSION_COOKIE = "wc_admin_session";

// 21 days — "remembered on this device".
const MAX_AGE_SECONDS = 60 * 60 * 24 * 21;

function adminPassword(): string | undefined {
  return process.env.ADMIN_PASSWORD || undefined;
}
function sessionSecret(): string | undefined {
  return process.env.SESSION_SECRET || undefined;
}

function constantTimeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

/** Fail-closed password check. False when ADMIN_PASSWORD is unset or input empty. */
export function verifyPassword(input: string): boolean {
  const expected = adminPassword();
  if (!expected || !input) return false;
  return constantTimeEqual(input, expected);
}

function sign(payload: string): string {
  return crypto.createHmac("sha256", sessionSecret()!).update(payload).digest("base64url");
}

/** Create a signed `admin.<issuedAtMs>.<hmac>` token. Throws if SESSION_SECRET unset. */
export function createSessionToken(nowMs: number): string {
  if (!sessionSecret()) throw new Error("SESSION_SECRET not set");
  const payload = `admin.${nowMs}`;
  return `${payload}.${sign(payload)}`;
}

/** Fail-closed token verification: valid signature, not expired, role=admin. */
export function verifySessionToken(token: string | undefined | null, nowMs: number): boolean {
  if (!token || !sessionSecret()) return false;
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  const [role, issuedAt, sig] = parts;
  if (role !== "admin") return false;
  if (!constantTimeEqual(sig, sign(`${role}.${issuedAt}`))) return false;
  const ageSeconds = (nowMs - Number(issuedAt)) / 1000;
  if (!Number.isFinite(ageSeconds) || ageSeconds < 0 || ageSeconds > MAX_AGE_SECONDS) return false;
  return true;
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: MAX_AGE_SECONDS,
  };
}

/** Read + verify the admin session cookie from a route-handler Request. */
export function requireAdmin(request: Request): boolean {
  const cookieHeader = request.headers.get("cookie") ?? "";
  const match = cookieHeader.match(new RegExp(`(?:^|;\\s*)${SESSION_COOKIE}=([^;]+)`));
  const token = match ? decodeURIComponent(match[1]) : null;
  return verifySessionToken(token, Date.now());
}
