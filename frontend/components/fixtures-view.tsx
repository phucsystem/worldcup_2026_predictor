"use client";

import { useEffect, useMemo, useState } from "react";
import type { UpcomingFixtures, FixtureRow as Fixture } from "@/lib/api";
import FixtureRow from "@/components/fixture-row";
import EmptyState from "@/components/empty-state";
import { FALLBACK_TZ, resolveTz } from "@/components/local-time";

type DayGroup = { key: string; fixtures: Fixture[] };

// Re-bucket fixtures by the calendar day in the given timezone. The backend
// pre-sorts by kickoff ascending, so insertion order stays chronological.
function groupByDay(fixtures: Fixture[], tz: string): DayGroup[] {
  const groups: DayGroup[] = [];
  const index = new Map<string, DayGroup>();
  for (const f of fixtures) {
    if (!f.kickoff_utc) continue;
    const key = new Date(f.kickoff_utc).toLocaleDateString("en-CA", { timeZone: tz });
    let g = index.get(key);
    if (!g) {
      g = { key, fixtures: [] };
      index.set(key, g);
      groups.push(g);
    }
    g.fixtures.push(f);
  }
  return groups;
}

function dayLabel(iso: string, tz: string): string {
  return new Date(iso).toLocaleDateString("en-AU", {
    timeZone: tz,
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

interface Props {
  upcoming: UpcomingFixtures;
}

export default function FixturesView({ upcoming }: Props) {
  // Group by the viewer's local day. First paint uses FALLBACK_TZ (matching the
  // server's Melbourne grouping → no hydration mismatch), then re-groups on mount.
  const [tz, setTz] = useState(FALLBACK_TZ);
  useEffect(() => {
    setTz(resolveTz());
  }, []);

  const days = useMemo(
    () => groupByDay(upcoming.days.flatMap((d) => d.fixtures), tz),
    [upcoming, tz],
  );

  if (days.length === 0) {
    return (
      <EmptyState
        message="No upcoming fixtures scheduled"
        subtext="Check back as the schedule fills in"
      />
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {days.map((day) => {
        const label = dayLabel(day.fixtures[0].kickoff_utc as string, tz);
        return (
          <section key={day.key} aria-label={label}>
            <h2
              className="text-xs font-semibold uppercase mb-3"
              style={{ color: "#A9B6D4", letterSpacing: "0.04em" }}
              suppressHydrationWarning
            >
              {label}
            </h2>
            <div className="flex flex-col gap-3">
              {day.fixtures.map((f) => (
                <FixtureRow key={f.fixture_id} fixture={f} showCountdown />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
