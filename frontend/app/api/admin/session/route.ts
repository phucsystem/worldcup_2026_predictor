import { cookies } from "next/headers";
import {
  SESSION_COOKIE,
  createSessionToken,
  sessionCookieOptions,
  verifyPassword,
} from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

// POST = login. Validates the password against ADMIN_PASSWORD; on success sets
// an HttpOnly session cookie. Fails closed (401) when ADMIN_PASSWORD is unset.
export async function POST(request: Request) {
  let password = "";
  try {
    const body = await request.json();
    password = typeof body?.password === "string" ? body.password : "";
  } catch {
    password = "";
  }

  const token = verifyPassword(password) ? createSessionToken(Date.now()) : undefined;
  if (!token) {
    return Response.json({ error: "Invalid password" }, { status: 401 });
  }

  const store = await cookies();
  store.set(SESSION_COOKIE, token, sessionCookieOptions());
  return new Response(null, { status: 204 });
}

// DELETE = logout. Clears the session cookie.
export async function DELETE() {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
  return new Response(null, { status: 204 });
}
