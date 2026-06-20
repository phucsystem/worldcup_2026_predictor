import type { FixtureRow as Fixture } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import Countdown from "@/components/countdown";
import LiveBadge from "@/components/live-badge";

// API status short-codes that mean a match is in progress.
const LIVE_STATUSES = new Set(["1H", "2H", "HT", "ET", "BT", "P", "LIVE", "INT"]);

function isLive(status: string | null): boolean {
  return !!status && LIVE_STATUSES.has(status);
}

function kickoffTime(iso: string | null): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "TBD";
  return d.toLocaleTimeString("en-AU", {
    timeZone: "Australia/Melbourne",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

interface Props {
  fixture: Fixture;
  showCountdown?: boolean;
  showScore?: boolean;
}

export default function FixtureRow({ fixture, showCountdown = false, showScore = false }: Props) {
  const live = isLive(fixture.status);
  const time = kickoffTime(fixture.kickoff_utc);

  return (
    <div
      className="flex items-center gap-4 px-4 py-3 border"
      style={{ backgroundColor: "#0A1B3D", borderColor: "#1E3157", borderRadius: "12px" }}
    >
      <div className="text-sm font-semibold tabular-nums shrink-0" style={{ color: "#FFFFFF", width: "3.5rem" }}>
        {time}
        <span className="block text-xs font-normal" style={{ color: "#6B7A9E" }}>
          AEST
        </span>
      </div>

      <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center gap-2 font-medium" style={{ color: "#FFFFFF" }}>
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} />
          <span className="truncate">{fixture.home_team ?? "TBD"}</span>
        </span>
        {showScore && fixture.home_score != null && fixture.away_score != null ? (
          <span className="font-bold tabular-nums px-1" style={{ color: "#FFFFFF" }}>
            {fixture.home_score}–{fixture.away_score}
          </span>
        ) : (
          <span className="text-xs" style={{ color: "#6B7A9E" }}>
            vs
          </span>
        )}
        <span className="inline-flex items-center gap-2 font-medium" style={{ color: "#FFFFFF" }}>
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} />
          <span className="truncate">{fixture.away_team ?? "TBD"}</span>
        </span>
      </div>

      <div className="flex items-center gap-3 shrink-0 text-xs">
        {fixture.group_name && (
          <span
            className="px-2 py-0.5 font-medium"
            style={{ backgroundColor: "#13294F", color: "#A9B6D4", borderRadius: "999px" }}
          >
            {fixture.group_name}
          </span>
        )}
        {live ? (
          <LiveBadge />
        ) : (
          showCountdown && <Countdown kickoffUtc={fixture.kickoff_utc} className="text-xs" />
        )}
      </div>
    </div>
  );
}
