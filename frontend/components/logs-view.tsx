"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { LogEvent, LogPage } from "@/lib/api";

const PAGE_SIZE = 50;
const SEARCH_DEBOUNCE_MS = 300;
const LIVE_POLL_MS = 10_000;

const LEVELS = [
  { value: "", label: "All" },
  { value: "info", label: "Info" },
  { value: "warn", label: "Warning" },
  { value: "error", label: "Error" },
] as const;

// Persisted levelname -> chip class (CRITICAL shares the error chip).
function chipClass(level: string): "info" | "warn" | "error" {
  const l = level.toUpperCase();
  if (l === "INFO") return "info";
  if (l === "WARNING") return "warn";
  return "error";
}

function LevelIcon({ kind }: { kind: "info" | "warn" | "error" }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2.2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (kind === "error") {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="10" />
        <line x1="15" y1="9" x2="9" y2="15" />
        <line x1="9" y1="9" x2="15" y2="15" />
      </svg>
    );
  }
  if (kind === "warn") {
    return (
      <svg {...common}>
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}

function formatClock(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString([], { hour12: false });
}

function relativeTime(iso: string, nowMs: number): string {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "";
  const secs = Math.max(0, Math.round((nowMs - t) / 1000));
  if (secs < 5) return "just now";
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

function hasDetail(ev: LogEvent): boolean {
  return ev.context != null && Object.keys(ev.context).length > 0;
}

function renderDetail(ctx: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(ctx)) {
    if (key === "traceback" || key === "stack") {
      parts.push(typeof value === "string" ? value : JSON.stringify(value, null, 2));
    } else {
      parts.push(`${key}  ${typeof value === "string" ? value : JSON.stringify(value)}`);
    }
  }
  return parts.join("\n");
}

export default function LogsView() {
  const [level, setLevel] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<LogPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [live, setLive] = useState(false);
  const [nowMs, setNowMs] = useState(0);
  const inFlight = useRef(false);

  // Debounce the free-text search; reset to page 1 when it settles.
  useEffect(() => {
    const id = setTimeout(() => {
      setQ(searchInput.trim());
      setOffset(0);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [searchInput]);

  const load = useCallback(async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
      });
      if (level) params.set("level", level);
      if (q) params.set("q", q);
      const res = await fetch(`/api/logs?${params.toString()}`, { cache: "no-store" });
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data: LogPage = await res.json();
      setPage(data);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      inFlight.current = false;
    }
  }, [level, q, offset]);

  useEffect(() => {
    load();
  }, [load]);

  // Live poll: refetch the current view on an interval (client-side only — no
  // websockets). The relative-time clock also needs a periodic tick.
  useEffect(() => {
    setNowMs(Date.now());
    const tick = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    if (!live) return;
    const id = setInterval(load, LIVE_POLL_MS);
    return () => clearInterval(id);
  }, [live, load]);

  const onLevel = (value: string) => {
    setLevel(value);
    setOffset(0);
  };

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const items = page?.items ?? [];
  const total = page?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const rangeStart = total === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, total);

  return (
    <>
      <div className="log-toolbar">
        <div className="toggle-group" role="group" aria-label="Filter by level">
          {LEVELS.map((lv) => (
            <button
              key={lv.value || "all"}
              type="button"
              className={level === lv.value ? "toggle-btn active" : "toggle-btn"}
              aria-pressed={level === lv.value}
              onClick={() => onLevel(lv.value)}
            >
              {lv.label}
            </button>
          ))}
        </div>
        <label className="log-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            type="search"
            placeholder="Search messages, sources…"
            aria-label="Search log messages"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </label>
        <button
          type="button"
          className="log-tail"
          aria-pressed={live}
          title="Auto-refresh newest events"
          onClick={() => setLive((v) => !v)}
        >
          <span className="dot" />
          <span className="lt-label">Live</span>
        </button>
      </div>

      <div className="table-container log-console">
        <table className="logs">
          <thead>
            <tr>
              <th scope="col" style={{ width: 140 }}>Time</th>
              <th scope="col" style={{ width: 96 }}>Level</th>
              <th scope="col" style={{ width: 200 }}>Source</th>
              <th scope="col">Message</th>
            </tr>
          </thead>
          <tbody>
            {items.map((ev) => {
              const kind = chipClass(ev.level);
              const detail = hasDetail(ev);
              const isOpen = expanded.has(ev.id);
              return (
                <RowGroup
                  key={ev.id}
                  ev={ev}
                  kind={kind}
                  detail={detail}
                  isOpen={isOpen}
                  nowMs={nowMs}
                  onToggle={() => toggleExpand(ev.id)}
                />
              );
            })}
          </tbody>
        </table>
        {!loading && !error && items.length === 0 && (
          <div className="log-noresults">No events match this filter.</div>
        )}
        {error && (
          <div className="log-noresults">Couldn’t load logs. Retrying on the next refresh.</div>
        )}
        {loading && items.length === 0 && !error && (
          <div className="log-noresults">Loading…</div>
        )}
      </div>

      {total > PAGE_SIZE && (
        <nav className="log-pagination" aria-label="Log pagination">
          <span className="log-page-range">
            {rangeStart}–{rangeEnd} of {total}
          </span>
          <span className="log-page-controls">
            <button
              type="button"
              className="log-page-btn"
              disabled={currentPage <= 1}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Prev
            </button>
            <span className="log-page-range" aria-current="page">
              Page {currentPage} / {totalPages}
            </span>
            <button
              type="button"
              className="log-page-btn"
              disabled={currentPage >= totalPages}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </span>
        </nav>
      )}
    </>
  );
}

function RowGroup({
  ev,
  kind,
  detail,
  isOpen,
  nowMs,
  onToggle,
}: {
  ev: LogEvent;
  kind: "info" | "warn" | "error";
  detail: boolean;
  isOpen: boolean;
  nowMs: number;
  onToggle: () => void;
}) {
  return (
    <>
      <tr className={kind === "error" ? "log-row is-error" : "log-row"}>
        <td className="c-time">
          <span className="log-time">
            {formatClock(ev.ts)}
            <span className="lt-rel">{relativeTime(ev.ts, nowMs)}</span>
          </span>
        </td>
        <td className="c-level">
          <span className={`lvl ${kind}`}>
            <LevelIcon kind={kind} />
            {kind === "warn" ? "Warn" : kind === "error" ? "Error" : "Info"}
          </span>
        </td>
        <td className="c-source">
          <span className="log-source">{ev.source}</span>
        </td>
        <td className="c-msg log-msg-cell">
          <span className="log-msg">{ev.message}</span>
          {detail && (
            <button className="log-expand" aria-expanded={isOpen} onClick={onToggle}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="9 18 15 12 9 6" />
              </svg>
              {ev.context && "traceback" in ev.context ? "Traceback" : "Context"}
            </button>
          )}
        </td>
      </tr>
      {detail && isOpen && (
        <tr className="log-detail-row">
          <td colSpan={4}>
            <pre className="log-detail">{renderDetail(ev.context as Record<string, unknown>)}</pre>
          </td>
        </tr>
      )}
    </>
  );
}
