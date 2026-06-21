# syntax=docker/dockerfile:1

# --- Builder ---
FROM node:24-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# --- Dev (hot reload) ---
# Used only by docker-compose.override.yml. Source is bind-mounted over /app at
# runtime; node_modules here (linux/musl) is kept alive by an anonymous volume so
# the host's darwin node_modules never shadows it.
#
# HMR over a macOS/Windows Docker bind mount: Next 16's `next dev` defaults to
# Turbopack, whose native file watcher does NOT receive inotify events across the
# Docker Desktop filesystem, so edits never recompile. We therefore run dev with
# `--webpack`, whose watcher honours WATCHPACK_POLLING — polling reliably picks up
# bind-mount changes. (Native `npm run dev` stays on Turbopack; this is dev-Docker
# only. Per Next docs, native local dev is still the fastest path.)
FROM node:24-alpine AS dev
WORKDIR /app

ENV NODE_ENV=development \
    PORT=3000 \
    WATCHPACK_POLLING=800

COPY package.json package-lock.json* ./
RUN npm ci

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--webpack"]

# --- Runner ---
FROM node:24-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# next standalone output bundles server + node_modules subset
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
