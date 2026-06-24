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

function sign(payload: string, key: string): string {
  return crypto.createHmac("sha256", key).update(payload).digest("base64url");
}

/**
 * Stateless session token `admin.<issuedAtMs>.<hmac>`, HMAC-keyed by the current
 * ADMIN_PASSWORD — the only credential, no separate signing secret. Rotating
 * ADMIN_PASSWORD invalidates existing sessions for free. Undefined when unset.
 */
export function createSessionToken(nowMs: number): string | undefined {
  const key = adminPassword();
  if (!key) return undefined;
  const payload = `admin.${nowMs}`;
  return `${payload}.${sign(payload, key)}`;
}

/** Fail-closed: valid signature (keyed by current password), role=admin, not expired. */
export function verifySessionToken(token: string | undefined | null, nowMs: number): boolean {
  const key = adminPassword();
  if (!token || !key) return false;
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  const [role, issuedAt, sig] = parts;
  if (role !== "admin") return false;
  if (!constantTimeEqual(sig, sign(`${role}.${issuedAt}`, key))) return false;
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
