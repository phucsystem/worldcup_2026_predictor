---
phase: 1
title: "Admin auth shell"
status: pending
priority: P1
dependencies: []
effort: "M"
---

# Phase 1: Admin auth shell

## Overview
A Next.js-owned single-admin session: a login page that verifies a password against an env secret server-side, sets a signed HttpOnly cookie, and `middleware.ts` that gates every `/admin/*` route and admin route handler. No user model, no backend auth changes.

## Requirements
- Functional: `/admin/login` form → POST → on match, set session cookie and redirect to `/admin`; on mismatch, show inline error. `/admin/*` without a valid session redirects to `/admin/login`. Logout clears the cookie. Session survives reloads (persistent cookie).
- Non-functional: password + signing secret are env-only; constant-time comparison; cookie is HttpOnly + `SameSite=Lax` + `Secure` in prod; no secret ever reaches the browser or the client bundle.

## Architecture
> **Next 16 convention (verified in `node_modules/next/dist/docs/.../version-16.md`):** the `middleware` file is deprecated and renamed to **`proxy`**. `proxy` runs on the **Node.js runtime only** (cannot be configured to Edge). This is exactly the chosen approach — Node runtime gives us `node:crypto` natively, no Web Crypto needed.

- **Session token:** signed value (HMAC-SHA256 over a fixed payload + issued-at, keyed by `SESSION_SECRET`) using `node:crypto` — no new dependency. Helper `lib/admin-auth.ts` (server-only, import `server-only`): `verifyPassword(input)`, `createSessionToken()`, `verifySessionToken(cookieValue)`, `requireAdmin(request)`, `SESSION_COOKIE` name + cookie options.
- **Env:** add `ADMIN_PASSWORD` and `SESSION_SECRET` to `frontend` env. Wire into `docker-compose.yml` frontend service env and `.env.example`. Both optional in code; when unset, login always fails closed (never default-allow).
- **Login flow:** `app/admin/login/page.tsx` (server component renders the form from `s13`) posting to a route handler `app/api/admin/session/route.ts` (`POST` = login, `DELETE` = logout). Login validates, then `cookies().set(...)`. Route handler (not a server action) for symmetry with logout and to keep the password POST off the RSC action channel.
- **Gate:** `proxy.ts` at `frontend/` root, exporting a `proxy` function (NOT `middleware`), with `matcher: ["/admin/:path*"]` excluding `/admin/login`. Runs on Node runtime → call `verifySessionToken` (node:crypto) directly; redirect to `/admin/login` on failure. The same `requireAdmin` helper re-checks in admin route handlers (defence-in-depth; used by Phase 3 APIs).
- **Admin shell layout:** `app/admin/layout.tsx` renders the admin top-nav (Admin badge, View site, Log out → `DELETE` then redirect) from `s14`. Admin pages live under `app/admin/`.

## Related Code Files
- Create: `frontend/lib/admin-auth.ts`, `frontend/proxy.ts`, `frontend/app/admin/layout.tsx`, `frontend/app/admin/login/page.tsx`, `frontend/app/api/admin/session/route.ts`, `frontend/app/admin/page.tsx` (placeholder, filled in Phase 3)
- Modify: `docker-compose.yml` (frontend env), `frontend/.env.example` (document `ADMIN_PASSWORD`, `SESSION_SECRET`), `infra`/VM `.env` (operator-set, not committed)
- Reference: `prototypes/s13-admin-login.html`, `prototypes/s14-admin-feedback.html` (shell + nav), `frontend/app/globals.css` (port `.admin-login*`, `.admin-badge`, `.admin-tabs` styles from `prototypes/components.css`)

## Implementation Steps
1. Read the bundled Next 16 docs: `version-16.md` (`middleware` → `proxy` rename, Node runtime), the authentication guide, and `cookies()` usage. (Confirmed during validation: `proxy` is Node-runtime, Edge not supported.)
2. Add `ADMIN_PASSWORD` + `SESSION_SECRET` to `.env.example`, `docker-compose.yml` frontend env, and document the VM `.env` requirement.
3. Write `lib/admin-auth.ts` (`import "server-only"`): constant-time password check (`crypto.timingSafeEqual`); sign/verify session token with `node:crypto` HMAC; `requireAdmin(request)` returning 401-or-ok; export cookie name + options (HttpOnly, SameSite=Lax, Secure when `NODE_ENV==='production'`, `maxAge` ~21d, `path=/`).
4. Write `app/api/admin/session/route.ts`: `POST` (validate password → set cookie → 204), `DELETE` (clear cookie). Fail closed when env unset.
5. Write `proxy.ts` exporting `proxy` (Node runtime), gating `/admin/:path*` (allow `/admin/login`), redirecting unauthenticated requests to `/admin/login`.
6. Build `app/admin/layout.tsx` + `app/admin/login/page.tsx` from the prototypes; port admin/login CSS into `globals.css`.
7. Add a minimal `app/admin/page.tsx` placeholder (filled in Phase 3) so the gate + shell are testable.

## Success Criteria
- [ ] Visiting `/admin` unauthenticated redirects to `/admin/login`.
- [ ] Correct password → redirected to `/admin`, cookie set; wrong password → inline error, no cookie.
- [ ] Session persists across reload; Log out clears it and re-gates `/admin`.
- [ ] With `ADMIN_PASSWORD` unset, login always fails (fail-closed); no secret appears in the client bundle (`grep` build output).
- [ ] `proxy.ts` (not `middleware.ts`) is used; build shows no deprecated-middleware warning.
- [ ] Lint + `tsc` clean.

## Risk Assessment
- **Next 16 `proxy` convention:** using the deprecated `middleware` filename would emit warnings and may break in a future minor. Mitigation: use `proxy.ts` + `proxy` export per `version-16.md`; success criterion asserts no deprecation warning.
- **Fail-open risk:** any code path that treats "no env / verify error" as authenticated is a critical bug. Mitigation: default-deny in `verifySessionToken`/`verifyPassword`/`requireAdmin`; unit-test all three with empty/garbage input.
- **Secret leakage:** importing `admin-auth.ts` from a client component would bundle the secret. Mitigation: `import "server-only"` guard; verify via build-output grep in success criteria.
