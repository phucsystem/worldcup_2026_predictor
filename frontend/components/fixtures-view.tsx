"use client";

import { useState } from "react";
import type { UpcomingFixtures, KnockoutBracket } from "@/lib/api";
import FixtureRow from "@/components/fixture-row";
import KnockoutBracketView from "@/components/knockout-bracket";
import EmptyState from "@/components/empty-state";

function dayLabel(iso: string): string {
  // `iso` is the backend's UTC grouping date (YYYY-MM-DD). Anchor at noon UTC
  // and format in UTC so the calendar day is identical at SSR and hydration
  // regardless of server/client timezone (this runs in a client component).
  return new Date(iso + "T12:00:00Z").toLocaleDateString("en-AU", {
    timeZone: "UTC",
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

type View = "upcoming" | "knockout";

interface Props {
  upcoming: UpcomingFixtures;
  knockout: KnockoutBracket;
}

export default function FixturesView({ upcoming, knockout }: Props) {
  const [view, setView] = useState<View>("upcoming");

  return (
    <div>
      <div role="tablist" aria-label="Fixtures view" className="inline-flex p-1 mb-6" style={{ backgroundColor: "#0A1B3D", borderRadius: "999px", border: "1px solid #1E3157" }}>
        {(["upcoming", "knockout"] as View[]).map((v) => {
          const active = view === v;
          return (
            <button
              key={v}
              role="tab"
              aria-selected={active}
              onClick={() => setView(v)}
              className="px-4 py-1.5 text-sm font-semibold capitalize transition-colors"
              style={{
                backgroundColor: active ? "#2D6BF6" : "transparent",
                color: active ? "#FFFFFF" : "#A9B6D4",
                borderRadius: "999px",
              }}
            >
              {v}
            </button>
          );
        })}
      </div>

      {view === "upcoming" ? (
        upcoming.days.length === 0 ? (
          <EmptyState message="No upcoming fixtures scheduled" subtext="Check back as the schedule fills in" />
        ) : (
          <div className="flex flex-col gap-8">
            {upcoming.days.map((day) => (
              <section key={day.date} aria-label={dayLabel(day.date)}>
                <h2 className="text-xs font-semibold uppercase mb-3" style={{ color: "#A9B6D4", letterSpacing: "0.04em" }}>
                  {dayLabel(day.date)}
                </h2>
                <div className="flex flex-col gap-3">
                  {day.fixtures.map((f) => (
                    <FixtureRow key={f.fixture_id} fixture={f} showCountdown />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )
      ) : (
        <KnockoutBracketView bracket={knockout} />
      )}
    </div>
  );
}
