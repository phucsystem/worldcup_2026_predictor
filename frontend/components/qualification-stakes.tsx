import type { StandingRow } from "@/lib/api";
import type { MatchStateName } from "@/lib/match";
import StandingsTable from "@/components/standings-table";

interface Props {
  groupName: string | null;
  rows: StandingRow[];
  state: MatchStateName;
}

// Real persisted standings slice for the match's group. v1 shows the CURRENT
// table (honestly labelled) — no fabricated "if the score holds" projection.
export default function QualificationStakes({ groupName, rows, state }: Props) {
  if (!groupName || rows.length === 0) return null;
  const heading =
    state === "finished" ? "What it means for the group" : "Group standings";
  const sub =
    state === "finished"
      ? "Standings after this result."
      : state === "live"
        ? "Current table — not yet updated for the in-play score."
        : "Current table going into this match.";
  return (
    <section aria-label={`${groupName} qualification picture`}>
      <h2 className="section-title">{heading}</h2>
      <p className="fs-sub" style={{ marginBottom: "var(--space-3)" }}>
        {sub}
      </p>
      <StandingsTable groupName={groupName} rows={rows} />
    </section>
  );
}
