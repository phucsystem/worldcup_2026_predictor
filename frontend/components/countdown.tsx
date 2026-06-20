"use client";

import { useEffect, useState } from "react";

interface Props {
  kickoffUtc: string | null;
  className?: string;
}

function format(msRemaining: number): string {
  const s = Math.floor(msRemaining / 1000);
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

/**
 * Live countdown to kickoff. Rolls to "LIVE" at zero. Decorative
 * (`aria-hidden`) — screen readers get the static kickoff time from the
 * surrounding fixture row. Renders a stable placeholder until mounted to avoid
 * hydration mismatch, and honors prefers-reduced-motion (no per-second churn).
 */
export default function Countdown({ kickoffUtc, className }: Props) {
  const [label, setLabel] = useState<string | null>(null);

  useEffect(() => {
    if (!kickoffUtc) return;
    const target = new Date(kickoffUtc).getTime();
    if (Number.isNaN(target)) return;

    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    const tick = () => {
      const diff = target - Date.now();
      setLabel(diff <= 0 ? "LIVE" : format(diff));
      return diff;
    };

    tick();
    // Reduced motion: update once per minute instead of every second.
    const interval = reduced ? 60_000 : 1_000;
    const id = window.setInterval(() => {
      if (tick() <= 0) window.clearInterval(id);
    }, interval);
    return () => window.clearInterval(id);
  }, [kickoffUtc]);

  if (label === null) {
    return (
      <span aria-hidden="true" className={className} style={{ color: "#6B7A9E" }}>
        —
      </span>
    );
  }

  const isLive = label === "LIVE";
  return (
    <span
      aria-hidden="true"
      className={className}
      style={{
        color: isLive ? "#FF5A5A" : "#4D8BFF",
        fontVariantNumeric: "tabular-nums",
        fontWeight: 600,
      }}
    >
      {isLive ? "LIVE" : `in ${label}`}
    </span>
  );
}
