import Link from "next/link";
import { listBriefs } from "@/lib/api";
import EmptyState from "@/components/empty-state";

export const dynamic = "force-dynamic";

function formatDay(d: string) {
  return new Date(d + "T00:00:00").getDate().toString().padStart(2, "0");
}

function formatMonthYear(d: string) {
  return new Date(d + "T00:00:00").toLocaleDateString("en-AU", {
    month: "long",
    year: "numeric",
  });
}

export const metadata: import("next").Metadata = {
  title: "Daily Brief Archive",
  description:
    "Browse past daily World Cup 2026 intelligence briefs — storylines, power rankings and qualification scenarios, day by day.",
  alternates: { canonical: "/archive" },
};

export default async function ArchivePage() {
  const briefs = await listBriefs();

  const groups: Record<string, typeof briefs> = {};
  for (const b of briefs) {
    const key = formatMonthYear(b.date);
    (groups[key] ??= []).push(b);
  }

  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <div className="flex items-baseline justify-between mb-8 flex-wrap gap-2">
        <h1 className="text-2xl font-bold" style={{ color: "#FFFFFF" }}>
          Archive
        </h1>
        <p
          className="text-xs font-semibold uppercase tracking-widest"
          style={{ color: "#6B7A9E", letterSpacing: "0.06em" }}
        >
          {briefs.length} {briefs.length === 1 ? "brief" : "briefs"}
        </p>
      </div>

      {briefs.length === 0 ? (
        <EmptyState
          message="No past briefs yet."
          subtext="Briefs are published daily at 7:00 AM AEST."
        />
      ) : (
        Object.entries(groups).map(([month, items]) => (
          <section key={month} className="mb-8" aria-label={`Briefs from ${month}`}>
            <p
              className="text-xs font-semibold uppercase tracking-widest mb-3"
              style={{ color: "#6B7A9E", letterSpacing: "0.06em" }}
            >
              {month}
            </p>
            <div
              className="rounded-xl border overflow-hidden"
              style={{ backgroundColor: "#0A1B3D", borderColor: "#1E3157", borderRadius: "12px" }}
            >
              {items.map((b, i) => (
                <Link
                  key={b.date}
                  href={`/brief/${b.date}`}
                  className="flex items-center gap-4 px-5 py-4 hover:bg-[#13294F] transition-colors"
                  style={{ borderBottom: i < items.length - 1 ? "1px solid #1E3157" : "none" }}
                  aria-label={`${formatMonthYear(b.date)} ${formatDay(b.date)}: ${b.title ?? "Daily Brief"}`}
                >
                  <span
                    className="text-xl font-bold tabular-nums shrink-0"
                    style={{ color: "#2D6BF6", width: "2rem" }}
                    aria-hidden="true"
                  >
                    {formatDay(b.date)}
                  </span>
                  <span className="flex-1 text-sm font-medium" style={{ color: "#FFFFFF" }}>
                    {b.title ?? "Daily Brief"}
                  </span>
                  <span aria-hidden="true" style={{ color: "#6B7A9E" }}>›</span>
                </Link>
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}
