import type { FixtureDetail } from "@/lib/api";
import LocalTime from "@/components/local-time";
import MatchBanner from "@/components/match-banner";

interface Props {
  fixture: FixtureDetail;
}

const STATUS_LABEL: Record<string, string> = {
  FT: "Full Time",
  AET: "After Extra Time",
  PEN: "Penalties",
};

// Finished hero — the .is-final variant of the shared .next-match banner, so it
// stays consistent with the live and preview heroes (matches prototype S-10).
export default function MatchHeroFinal({ fixture }: Props) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const statusLabel = STATUS_LABEL[(fixture.status ?? "").toUpperCase()] ?? "Full Time";
  const context = fixture.group_name ?? fixture.stage ?? null;

  return (
    <section
      className="next-match is-final"
      data-flag-bg
      aria-label={`Full time: ${fixture.home_team ?? "TBD"} ${hs}, ${fixture.away_team ?? "TBD"} ${as}`}
    >
      <MatchBanner
        fixture={fixture}
        variant="final"
        eyebrowLabel={`${statusLabel}${context ? ` · ${context}` : ""}`}
        events={fixture.events}
        meta={<LocalTime iso={fixture.kickoff_utc} mode="dayTime" withZone />}
        watchLabel="Watch highlights on SBS"
        shareLabel="Share result"
        shareTitle={`${fixture.home_team ?? "TBD"} ${hs}–${as} ${fixture.away_team ?? "TBD"}`}
      />
    </section>
  );
}
