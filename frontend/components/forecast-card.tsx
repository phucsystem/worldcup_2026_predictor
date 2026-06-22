import type { Forecast } from "@/lib/match";

interface Props {
  forecast: Forecast;
  homeTeam: string;
  awayTeam: string;
}

// Pre-kickoff win-probability forecast. All content — the split and the factor
// leans/reasoning — is model-generated (lib/api FixtureDetail.forecast); this
// component is presentational and adds no data of its own.
export default function ForecastCard({ forecast, homeTeam, awayTeam }: Props) {
  const { home_pct: homePct, draw_pct: drawPct, away_pct: awayPct, factors } = forecast;
  const leadHome = homePct >= awayPct;
  return (
    <section
      className="forecast-card"
      aria-label="Experimental pre-match win-probability forecast — model preview"
    >
      <div className="fc-head">
        <h2 className="fc-title">Win probability · before kickoff</h2>
        <span className="fc-tag">Model preview · experimental</span>
      </div>
      <div
        className="fc-bar"
        role="img"
        aria-label={`Pre-match win probability: ${homeTeam} ${homePct} percent, draw ${drawPct} percent, ${awayTeam} ${awayPct} percent`}
      >
        <span className={`fc-seg home${leadHome ? " lead" : ""}`} style={{ width: `${homePct}%` }}>
          {homePct}%
        </span>
        <span className="fc-seg draw" style={{ width: `${drawPct}%` }}>
          {drawPct}%
        </span>
        <span className={`fc-seg away${leadHome ? "" : " lead"}`} style={{ width: `${awayPct}%` }}>
          {awayPct}%
        </span>
      </div>
      <div className="fc-legend">
        <span className={leadHome ? "lead" : undefined}>
          <i className="fc-key home" /> {homeTeam} {homePct}%{leadHome ? " · most likely" : ""}
        </span>
        <span>
          <i className="fc-key draw" /> Draw {drawPct}%
        </span>
        <span className={leadHome ? undefined : "lead"}>
          <i className="fc-key away" /> {awayTeam} {awayPct}%{leadHome ? "" : " · most likely"}
        </span>
      </div>

      <p className="fc-subhead">What drives this forecast</p>
      <ul className="fc-factors">
        {factors.map((f) => (
          <li className="fc-factor" key={f.name}>
            <span className="ff-name">{f.name}</span>
            <span className={`ff-lean ${f.lean}`}>
              {f.lean === "home" ? `Favours ${homeTeam}` : f.lean === "away" ? `Edge ${awayTeam}` : "Even"}
            </span>
            <span className="ff-why">{f.why}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
