import type { RecentResult } from "@/lib/api";
import TeamFlag from "@/components/team-flag";

interface Side {
  team: string | null;
  logo: string | null;
  results: RecentResult[];
}

interface Props {
  home: Side;
  away: Side;
}

function FormSide({ team, logo, results }: Side) {
  const last5 = results.slice(0, 5);
  return (
    <div className="form-side">
      <div className="fs-team">
        <TeamFlag team={team} logo={logo} size={24} />
        {team ?? "—"}
      </div>
      {last5.length > 0 ? <div className="fs-sub">Last {last5.length}</div> : null}
      <div className="fs-form-line">
        {last5.length === 0 ? (
          <span className="fs-sub">No recent results</span>
        ) : (
          last5.map((r, i) => (
            <span className={`fs-pip ${r.outcome.toLowerCase()}`} key={i}>
              {r.outcome}
            </span>
          ))
        )}
      </div>
    </div>
  );
}

export default function FormCompare({ home, away }: Props) {
  const hasAny = home.results.length > 0 || away.results.length > 0;
  if (!hasAny) return null;
  return (
    <div className="form-compare">
      <FormSide {...home} />
      <FormSide {...away} />
    </div>
  );
}
