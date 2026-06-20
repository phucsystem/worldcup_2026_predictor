import type { StandingRow } from "@/lib/api";
import PositionDelta from "@/components/position-delta";
import QualificationBadge from "@/components/qualification-badge";
import type { QualificationStatus } from "@/components/qualification-badge";
import TeamFlag from "@/components/team-flag";
import Sparkline from "@/components/sparkline";

interface Props {
  groupName: string;
  rows: StandingRow[];
}

function toQualStatus(value: string | null): QualificationStatus {
  if (value === "qualified" || value === "eliminated" || value === "contention") return value;
  // null (pre-tournament / seed rows) → render as neutral contention state
  return null;
}

export default function StandingsTable({ groupName, rows }: Props) {
  return (
    <section aria-label={`${groupName} standings`} className="mb-8">
      <h2
        className="text-xs font-semibold uppercase mb-3"
        style={{ color: "#A9B6D4", letterSpacing: "0.04em" }}
      >
        {groupName}
      </h2>
      <div className="overflow-x-auto" style={{ WebkitOverflowScrolling: "touch" }}>
        <table
          className="w-full text-sm"
          style={{
            backgroundColor: "#0A1B3D",
            borderRadius: "12px",
            borderCollapse: "collapse",
            fontVariantNumeric: "tabular-nums",
            minWidth: "480px",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "1px solid #1E3157" }}>
              <th scope="col" className="text-left px-4 py-3 font-medium" style={{ color: "#6B7A9E", width: "2rem" }}>#</th>
              <th scope="col" className="text-left px-4 py-3 font-medium" style={{ color: "#6B7A9E" }}>Team</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>P</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>W</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>D</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>L</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>GF</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>GA</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>GD</th>
              <th scope="col" className="text-right px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>Pts</th>
              <th scope="col" className="text-center px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>Form</th>
              <th scope="col" className="text-center px-3 py-3 font-medium" style={{ color: "#6B7A9E" }}>±</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const qual = toQualStatus(row.qualification);
              return (
                <tr
                  key={`${row.team}-${i}`}
                  className="transition-colors hover:bg-[#13294F]"
                  style={{ borderBottom: i < rows.length - 1 ? "1px solid #1E3157" : "none" }}
                >
                  <td className="px-4 py-3 font-semibold" style={{ color: "#6B7A9E" }}>
                    <span className="flex items-center gap-1">
                      {row.position ?? i + 1}
                      <QualificationBadge status={qual} />
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium" style={{ color: "#FFFFFF" }}>
                    <span className="flex items-center gap-2">
                      <TeamFlag team={row.team} logo={row.logo} size={18} />
                      {row.team ?? "—"}
                    </span>
                  </td>
                  <td className="text-right px-3 py-3" style={{ color: "#A9B6D4" }}>{row.played ?? 0}</td>
                  <td className="text-right px-3 py-3" style={{ color: "#2BD37E" }}>{row.won ?? 0}</td>
                  <td className="text-right px-3 py-3" style={{ color: "#F4B740" }}>{row.drawn ?? 0}</td>
                  <td className="text-right px-3 py-3" style={{ color: "#FF5A5A" }}>{row.lost ?? 0}</td>
                  <td className="text-right px-3 py-3" style={{ color: "#A9B6D4" }}>{row.gf ?? 0}</td>
                  <td className="text-right px-3 py-3" style={{ color: "#A9B6D4" }}>{row.ga ?? 0}</td>
                  <td className="text-right px-3 py-3" style={{ color: "#A9B6D4" }}>
                    {row.gd != null ? (row.gd > 0 ? `+${row.gd}` : row.gd) : 0}
                  </td>
                  <td className="text-right px-3 py-3 font-bold" style={{ color: "#FFFFFF" }}>{row.points ?? 0}</td>
                  <td className="px-3 py-3">
                    <span className="flex justify-center">
                      <Sparkline results={row.recent_results ?? []} />
                    </span>
                  </td>
                  <td className="text-center px-3 py-3">
                    <PositionDelta position={row.position} prevPosition={row.prev_position} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
