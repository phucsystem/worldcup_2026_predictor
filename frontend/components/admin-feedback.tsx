"use client";

import { useMemo, useState } from "react";
import type { Feedback, FeedbackStatus, FeedbackTopic } from "@/lib/api";

type Filter = "all" | FeedbackStatus;

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "new", label: "New" },
  { key: "done", label: "Done" },
  { key: "wont", label: "Won't do" },
];

const STATUS_LABEL: Record<FeedbackStatus, string> = { new: "New", done: "Done", wont: "Won't do" };
const TOPIC_LABEL: Record<FeedbackTopic, string> = { bug: "Bug", feature: "Feature", other: "Other" };

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return days === 1 ? "yesterday" : `${days}d ago`;
}

export default function AdminFeedback({ initial }: { initial: Feedback[] }) {
  const [items, setItems] = useState<Feedback[]>(initial);
  const [filter, setFilter] = useState<Filter>("all");
  const [toast, setToast] = useState<string | null>(null);

  const counts = useMemo(() => {
    const c = { all: items.length, new: 0, done: 0, wont: 0 };
    for (const it of items) c[it.status]++;
    return c;
  }, [items]);

  const visible = filter === "all" ? items : items.filter((it) => it.status === filter);

  async function setStatus(id: number, status: FeedbackStatus) {
    const prev = items;
    // Optimistic update.
    setItems((list) =>
      list.map((it) =>
        it.id === id
          ? { ...it, status, resolved_at: status === "new" ? null : new Date().toISOString() }
          : it,
      ),
    );
    const res = await fetch(`/api/admin/feedback/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (res.ok) {
      setToast(status === "new" ? "Reopened" : status === "done" ? "Marked done" : "Marked won't do");
      setTimeout(() => setToast(null), 2600);
    } else {
      setItems(prev); // revert on failure
      setToast("Couldn't update — try again");
      setTimeout(() => setToast(null), 2600);
    }
  }

  return (
    <>
      <div className="fb-filterbar" role="group" aria-label="Filter feedback by status">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className="fb-fstat"
            data-fb-filter={f.key}
            aria-pressed={filter === f.key}
            onClick={() => setFilter(f.key)}
          >
            <span className="fs-num">{counts[f.key]}</span> {f.label}
          </button>
        ))}
      </div>

      <div className="fb-list">
        {visible.map((it) => {
          const resolved = it.status !== "new";
          return (
            <article
              key={it.id}
              className={`fb-item${it.status === "done" ? " is-done" : ""}${it.status === "wont" ? " is-wont" : ""}`}
              data-status={it.status}
            >
              <div className="fb-it-head">
                {it.topic && (
                  <span className={`fb-topic ${it.topic}`}>
                    <span className="dot" />
                    {TOPIC_LABEL[it.topic]}
                  </span>
                )}
                <span className="fb-it-meta">
                  {it.page && <code>{it.page}</code>}
                  <span>{relativeTime(it.created_at)}</span>
                </span>
                <span className={`fb-status ${it.status}`}>
                  <span className="dot" />
                  {STATUS_LABEL[it.status]}
                </span>
              </div>
              <p className="fb-it-text">{it.message}</p>
              <div className="fb-it-actions">
                {resolved ? (
                  <button className="fb-act reopen" onClick={() => setStatus(it.id, "new")}>
                    ↺ Reopen
                  </button>
                ) : (
                  <>
                    <button className="fb-act wont" onClick={() => setStatus(it.id, "wont")}>
                      Won&apos;t do
                    </button>
                    <button className="fb-act done" onClick={() => setStatus(it.id, "done")}>
                      ✓ Mark done
                    </button>
                  </>
                )}
              </div>
            </article>
          );
        })}

        {visible.length === 0 && (
          <div className="fb-empty">
            <strong>Nothing here</strong>
            No feedback with this status yet.
          </div>
        )}
      </div>

      {toast && (
        <div className="fb-toast" role="status">
          <span className="dot" />
          {toast}
        </div>
      )}
    </>
  );
}
