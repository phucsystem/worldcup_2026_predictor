"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import type { ResultWidgetRow } from "@/lib/results";
import TeamFlag from "@/components/team-flag";
import { finishedStatusLabel } from "@/lib/match";

function accuracyTier(pct: number): "high" | "mid" | "low" {
  if (pct >= 67) return "high";
  if (pct >= 34) return "mid";
  return "low";
}

/**
 * Latest Results — ABC-style center-anchored list with a "Display in Groups"
 * toggle. Inline `order` is set on every row/header so server and client markup
 * are identical — no hydration mismatch.
 */
export default function ResultsWidget({
  rows,
  viewAllHref,
}: {
  rows: ResultWidgetRow[];
  viewAllHref?: string; // when set, render a "View all results →" link in the header
}) {
  const [grouped, setGrouped] = useState(false);
  // Which date's forecast summary is open. Hover opens transiently; a click
  // pins it open (and toggles closed) so touch users get the same summary.
  const [openDate, setOpenDate] = useState<string | null>(null);
  const [pinnedDate, setPinnedDate] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!pinnedDate) return;
    function onDocClick(event: MouseEvent) {
      if (!listRef.current?.contains(event.target as Node)) {
        setPinnedDate(null);
        setOpenDate(null);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setPinnedDate(null);
        setOpenDate(null);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [pinnedDate]);

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
    // Per-date forecast accuracy = correct forecasts / matches that carried one.
    // `forecasts` backs the hover/click summary popover.
    type ForecastEntry = { row: ResultWidgetRow; correct: boolean };
    type DateRow = {
      briefDate: string;
      dateLabel: string;
      forecastHits: number;
      forecastTotal: number;
      forecasts: ForecastEntry[];
    };
    const dateRows: DateRow[] = [];
    for (const row of rows) {
      let dateRow = dateRows.find((entry) => entry.briefDate === row.briefDate);
      if (!dateRow) {
        dateRow = {
          briefDate: row.briefDate,
          dateLabel: row.dateLabel,
          forecastHits: 0,
          forecastTotal: 0,
          forecasts: [],
        };
        dateRows.push(dateRow);
      }
      if (row.forecastCorrect !== null) {
        dateRow.forecastTotal += 1;
        if (row.forecastCorrect) dateRow.forecastHits += 1;
        dateRow.forecasts.push({ row, correct: row.forecastCorrect });
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
        {viewAllHref && (
          <Link className="next-two-all" href={viewAllHref}>
            View all results →
          </Link>
        )}
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

      <div className="rw-list" ref={listRef}>
        {rows.map((row) => {
          const winHome = row.winner === "home";
          const winAway = row.winner === "away";
          const showPen = row.status === "PEN";
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
              <span className={`mr-score${winHome ? " win" : ""}`}>
                {row.homeScore}
                {showPen && row.homePen != null && <span className="mr-pen">({row.homePen})</span>}
              </span>
              <span className="mr-center">
                <span className="mr-group">{row.group}</span>
                <span className="mr-status">{finishedStatusLabel(row.status)}</span>
              </span>
              <span className={`mr-score${winAway ? " win" : ""}`}>
                {row.awayScore}
                {showPen && row.awayPen != null && <span className="mr-pen">({row.awayPen})</span>}
              </span>
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

        {dates.map((dateRow, dateIndex) => {
          const pct =
            dateRow.forecastTotal > 0
              ? Math.round((dateRow.forecastHits / dateRow.forecastTotal) * 100)
              : null;
          const summaryOpen = openDate === dateRow.briefDate || pinnedDate === dateRow.briefDate;
          return (
            <div
              key={dateRow.briefDate}
              className={`rw-date-header${dateIndex === 0 ? " first" : ""}`}
              style={{ order: dateIndex * 100 }}
            >
              <span className="rw-dh-label">{dateRow.dateLabel}</span>
              {pct !== null && (
                <span className="rw-dh-acc-wrap">
                <button
                  type="button"
                  className={`rw-dh-acc acc-${accuracyTier(pct)}${summaryOpen ? " open" : ""}`}
                  aria-expanded={summaryOpen}
                  aria-label={`Model forecast ${dateRow.forecastHits} of ${dateRow.forecastTotal} results correctly on ${dateRow.dateLabel}. Show breakdown.`}
                  onMouseEnter={() => setOpenDate(dateRow.briefDate)}
                  onMouseLeave={() => setOpenDate(null)}
                  onFocus={() => setOpenDate(dateRow.briefDate)}
                  onBlur={() => setOpenDate(null)}
                  onClick={() =>
                    setPinnedDate((current) =>
                      current === dateRow.briefDate ? null : dateRow.briefDate,
                    )
                  }
                >
                  <span className="rw-dh-acc-icon" aria-hidden="true">◎</span>
                  <span className="rw-dh-acc-frac">
                    {dateRow.forecastHits}/{dateRow.forecastTotal}
                  </span>
                  <span className="rw-dh-acc-pct">{pct}%</span>
                </button>
                {summaryOpen && (
                  <div className="rw-dh-pop" role="dialog" aria-label={`Forecast summary for ${dateRow.dateLabel}`}>
                    <div className="rw-dh-pop-head">
                      <span className="rw-dh-pop-title">Forecast · {dateRow.dateLabel}</span>
                      <span className={`rw-dh-pop-rate acc-${accuracyTier(pct)}`}>
                        {dateRow.forecastHits}/{dateRow.forecastTotal} correct · {pct}%
                      </span>
                    </div>
                    <ul className="rw-dh-pop-list">
                      {dateRow.forecasts.map((entry) => (
                        <li
                          key={entry.row.key}
                          className={`rw-dh-pop-item${entry.correct ? " hit" : " miss"}`}
                        >
                          <span className="rw-dh-pop-mark" aria-hidden="true">
                            {entry.correct ? "✓" : "✗"}
                          </span>
                          <span className="rw-dh-pop-match">
                            {entry.row.home} {entry.row.homeScore}–{entry.row.awayScore} {entry.row.away}
                          </span>
                          <span className="rw-dh-pop-verdict">
                            {entry.correct ? "Called" : "Missed"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
