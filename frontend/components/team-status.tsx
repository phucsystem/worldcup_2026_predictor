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

// Fact-based pre-match status: one objective line + who's suspended, one booking
// away, or injured/doubtful, per team. Card flags are replayed from stored card
// events; injuries come from API-Football. Each row carries a reason badge so the
// cause (red card / yellow / injury) is explicit.
// Icon-only badges keep rows compact; the full reason rides along as a tooltip +
// screen-reader label so nothing is lost.
const CARD_BADGES: Record<string, { icon: string; label: string }> = {
  "red-card": { icon: "🟥", label: "Red card" },
  "yellow-accumulation": { icon: "🟨", label: "Second yellow" },
  "one-yellow": { icon: "🟨", label: "One yellow" },
};

function badgeFor(p: PlayerStatus): { icon: string; label: string } {
  if (p.status === "injured") return { icon: "🤕", label: p.reason || "Injured" };
  if (p.status === "doubtful") return { icon: "❓", label: p.reason ? `Doubtful · ${p.reason}` : "Doubtful" };
  return CARD_BADGES[p.reason] ?? { icon: "", label: p.reason };
}

function PlayerRow({ p }: { p: PlayerStatus }) {
  const badge = badgeFor(p);
  return (
    <li className={`tps-player${p.key_player ? " key" : ""}`}>
      {p.key_player ? (
        <span className="tps-star" aria-hidden="true">
          ★
        </span>
      ) : null}
      <span className="tps-name">{p.player}</span>
      {p.key_player ? <span className="sr-only"> (key player)</span> : null}
      {badge.icon ? (
        <span className="tps-badge" title={badge.label} aria-hidden="true">
          {badge.icon}
        </span>
      ) : null}
      {badge.label ? <span className="sr-only"> — {badge.label}</span> : null}
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
      {status && status.injured.length > 0 ? (
        <div className="ts-group">
          <div className="ts-group-label">Injured / doubtful</div>
          <ul className="ts-players">
            {status.injured.map((p) => (
              <PlayerRow key={p.player} p={p} />
            ))}
          </ul>
        </div>
      ) : null}
      {status &&
      status.unavailable.length === 0 &&
      status.at_risk.length === 0 &&
      status.injured.length === 0 ? (
        <div className="fs-sub">No suspensions or injuries</div>
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
