"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ResultWidgetRow } from "@/lib/results";
import TeamFlag from "@/components/team-flag";

/**
 * Latest Results — ABC-style center-anchored list with a "Display in Groups"
 * toggle. Inline `order` is set on every row/header so server and client markup
 * are identical — no hydration mismatch.
 */
export default function ResultsWidget({ rows }: { rows: ResultWidgetRow[] }) {
  const [grouped, setGrouped] = useState(false);

  const groups = useMemo(() => {
    const groupNames: string[] = [];
    for (const row of rows) if (!groupNames.includes(row.group)) groupNames.push(row.group);
    return groupNames.sort((firstGroup, secondGroup) => {
      const firstLatestDate = rows
        .filter((row) => row.group === firstGroup)
        .reduce((latestDate, row) => row.briefDate > latestDate ? row.briefDate : latestDate, "");
      const secondLatestDate = rows
        .filter((row) => row.group === secondGroup)
        .reduce((latestDate, row) => row.briefDate > latestDate ? row.briefDate : latestDate, "");
      return secondLatestDate.localeCompare(firstLatestDate) || firstGroup.localeCompare(secondGroup);
    });
  }, [rows]);

  const dates = useMemo(() => {
    const dateRows: Array<{ briefDate: string; dateLabel: string }> = [];
    for (const row of rows) {
      if (!dateRows.some((dateRow) => dateRow.briefDate === row.briefDate)) {
        dateRows.push({ briefDate: row.briefDate, dateLabel: row.dateLabel });
      }
    }
    return dateRows.sort((firstDate, secondDate) => secondDate.briefDate.localeCompare(firstDate.briefDate));
  }, [rows]);

  const groupedOrder = useMemo(() => {
    const groupCounters: Record<number, number> = {};
    const orderByKey: Record<string, number> = {};
    rows
      .slice()
      .sort((firstRow, secondRow) => secondRow.briefDate.localeCompare(firstRow.briefDate))
      .forEach((row) => {
        const groupIndex = groups.indexOf(row.group);
        groupCounters[groupIndex] = (groupCounters[groupIndex] || 0) + 1;
        orderByKey[row.key] = groupIndex * 100 + groupCounters[groupIndex];
      });
    return orderByKey;
  }, [groups, rows]);

  const dateOrder = useMemo(() => {
    const dateCounters: Record<number, number> = {};
    const orderByKey: Record<string, number> = {};
    rows
      .slice()
      .sort((firstRow, secondRow) => {
        const dateDiff = secondRow.briefDate.localeCompare(firstRow.briefDate);
        return dateDiff || firstRow.group.localeCompare(secondRow.group);
      })
      .forEach((row) => {
        const dateIndex = dates.findIndex((dateRow) => dateRow.briefDate === row.briefDate);
        dateCounters[dateIndex] = (dateCounters[dateIndex] || 0) + 1;
        orderByKey[row.key] = dateIndex * 100 + dateCounters[dateIndex];
      });
    return orderByKey;
  }, [dates, rows]);

  if (!rows || rows.length === 0) return null;

  return (
    <section className={`results-widget${grouped ? " grouped" : ""}${!grouped ? " has-date-headers" : ""}`}>
      <div className="rw-head">
        <h2 className="rw-title">Latest Results</h2>
      </div>

      <label className="rw-toggle-bar">
        <span className="rw-tg-label">Display in Groups</span>
        <input
          type="checkbox"
          hidden
          checked={grouped}
          onChange={(e) => setGrouped(e.target.checked)}
        />
        <span className="rw-switch" aria-hidden="true" />
        <span className="rw-tg-state">{grouped ? "On" : "Off"}</span>
      </label>

      <div className="rw-list">
        {rows.map((row) => {
          const winHome = row.winner === "home";
          const winAway = row.winner === "away";
          return (
            <Link
              key={row.key}
              href={row.fixtureId != null ? `/match/${row.fixtureId}` : `/brief/${row.briefDate}`}
              className={`match-row${winHome ? " winner-home" : ""}${winAway ? " winner-away" : ""}`}
              style={{ order: grouped ? groupedOrder[row.key] : dateOrder[row.key] }}
            >
              <span className="mr-date">{row.dateLabel}</span>
              <span className={`mr-team home${winAway ? " lose" : ""}`}>
                <span className="mr-name">{row.home}</span>
                <TeamFlag team={row.home} size={18} />
              </span>
              <span className={`mr-score${winHome ? " win" : ""}`}>{row.homeScore}</span>
              <span className="mr-center">
                <span className="mr-group">{row.group}</span>
                <span className="mr-status">Full Time</span>
              </span>
              <span className={`mr-score${winAway ? " win" : ""}`}>{row.awayScore}</span>
              <span className={`mr-team away${winHome ? " lose" : ""}`}>
                <TeamFlag team={row.away} size={18} />
                <span className="mr-name">{row.away}</span>
              </span>
              <span className="mr-arrow">→</span>
            </Link>
          );
        })}

        {groups.map((groupName, groupIndex) => (
          <div key={groupName} className="rw-group-header" style={{ order: groupIndex * 100 }}>
            {groupName}
          </div>
        ))}

        {dates.map((dateRow, dateIndex) => (
          <div
            key={dateRow.briefDate}
            className={`rw-date-header${dateIndex === 0 ? " first" : ""}`}
            style={{ order: dateIndex * 100 }}
          >
            {dateRow.dateLabel}
          </div>
        ))}
      </div>
    </section>
  );
}
