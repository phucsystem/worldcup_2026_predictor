import type { PlayerStatus, TeamStatus } from "@/lib/api";
import TeamFlag from "@/components/team-flag";

interface Side {
  team: string | null;
  logo: string | null;
  status: TeamStatus | null;
}

interface Props {
  home: Side;
  away: Side;
}

// Fact-based pre-match status: one objective line + who's suspended / one booking
// away, per team. Suspensions are derived from stored card events only; no
// injury/fitness data is implied (hence "No suspensions", not "Full squad").
function PlayerRow({ p }: { p: PlayerStatus }) {
  return (
    <li className={`tps-player${p.key_player ? " key" : ""}`}>
      {p.key_player ? (
        <span className="tps-star" aria-hidden="true">
          ★
        </span>
      ) : null}
      <span className="tps-name">{p.player}</span>
      {p.key_player ? <span className="sr-only"> (key player)</span> : null}
    </li>
  );
}

function StatusSide({ team, logo, status }: Side) {
  return (
    <div className="ts-side">
      <div className="ts-team">
        <TeamFlag team={team} logo={logo} size={24} />
        {team ?? "—"}
      </div>
      {status?.objective ? (
        <span className={`sk-note ${status.objective_css}`}>{status.objective}</span>
      ) : null}
      {status && status.unavailable.length > 0 ? (
        <div className="ts-group">
          <div className="ts-group-label">Suspended</div>
          <ul className="ts-players">
            {status.unavailable.map((p) => (
              <PlayerRow key={p.player} p={p} />
            ))}
          </ul>
        </div>
      ) : null}
      {status && status.at_risk.length > 0 ? (
        <div className="ts-group">
          <div className="ts-group-label">One booking away</div>
          <ul className="ts-players">
            {status.at_risk.map((p) => (
              <PlayerRow key={p.player} p={p} />
            ))}
          </ul>
        </div>
      ) : null}
      {status && status.unavailable.length === 0 && status.at_risk.length === 0 ? (
        <div className="fs-sub">No suspensions</div>
      ) : null}
    </div>
  );
}

export default function TeamStatusSection({ home, away }: Props) {
  if (!home.status && !away.status) return null;
  return (
    <section aria-label="Team status">
      <h2 className="section-title">Team status</h2>
      <div className="team-status">
        <StatusSide {...home} />
        <StatusSide {...away} />
      </div>
    </section>
  );
}
