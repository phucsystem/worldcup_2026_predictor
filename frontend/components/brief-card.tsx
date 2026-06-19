import Link from "next/link";
import type { BriefSummary } from "@/lib/api";

function formatDate(d: string) {
  return new Date(d + "T00:00:00").toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

interface HeroProps {
  brief: BriefSummary;
  dateLabel?: string;
}

export function HeroBriefCard({ brief, dateLabel }: HeroProps) {
  return (
    <Link
      href={`/brief/${brief.date}`}
      className="block group"
      aria-label={`Read brief: ${brief.title ?? "Today's Brief"}`}
    >
      <article
        className="p-6 border transition-colors"
        style={{
          backgroundColor: "#0A1B3D",
          borderColor: "#1E3157",
          borderRadius: "12px",
          outline: "none",
        }}
      >
        {dateLabel && (
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}>
            {dateLabel}
          </p>
        )}
        <h2
          className="font-extrabold mb-3 group-hover:text-blue-400 transition-colors"
          style={{ color: "#FFFFFF", lineHeight: 1.15, fontSize: "clamp(2rem, 3vw, 2.5rem)" }}
        >
          {brief.title ?? "Today's Brief"}
        </h2>
        {brief.summary && (
          <p className="mb-4 text-lg" style={{ color: "#A9B6D4", lineHeight: 1.5 }}>
            {brief.summary}
          </p>
        )}
        <span
          className="text-sm font-semibold"
          style={{ color: "#2D6BF6" }}
          aria-hidden="true"
        >
          Read brief →
        </span>
      </article>
    </Link>
  );
}

interface CompactProps {
  brief: BriefSummary;
}

export function CompactBriefCard({ brief }: CompactProps) {
  return (
    <Link
      href={`/brief/${brief.date}`}
      className="block group"
      aria-label={`Read brief from ${formatDate(brief.date)}: ${brief.title ?? "Daily Brief"}`}
    >
      <article
        className="p-4 border h-full transition-colors"
        style={{
          backgroundColor: "#0A1B3D",
          borderColor: "#1E3157",
          borderRadius: "12px",
        }}
      >
        <p className="text-xs mb-1" style={{ color: "#6B7A9E" }}>
          {formatDate(brief.date)}
        </p>
        <p
          className="text-sm font-medium group-hover:text-blue-400 transition-colors"
          style={{ color: "#FFFFFF" }}
        >
          {brief.title ?? "Daily Brief"}
        </p>
        {brief.summary && (
          <p className="text-xs mt-1 line-clamp-2" style={{ color: "#A9B6D4" }}>
            {brief.summary}
          </p>
        )}
      </article>
    </Link>
  );
}
