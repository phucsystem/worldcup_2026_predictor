import type { RecentResult } from "@/lib/api";
import { sparklinePath, OUTCOME_VALUE } from "@/lib/sparkline";

interface Props {
  results: RecentResult[];
  width?: number;
  height?: number;
}

const DOT_COLOR: Record<string, string> = {
  W: "#2BD37E",
  D: "#F4B740",
  L: "#FF5A5A",
};

// Recent-form line for a team. `results` arrive most-recent-first; we render
// oldest→newest (left→right). Graceful degrade: nothing drawn for < 2 results.
export default function Sparkline({ results, width = 70, height = 20 }: Props) {
  const ordered = [...results].reverse();
  const values = ordered.map((r) => OUTCOME_VALUE[r.outcome] ?? 1);
  const points = sparklinePath(values, width, height);
  if (!points) return null;

  const coords = points.split(" ").map((c) => c.split(",").map(Number));
  const label = `form: ${ordered
    .map((r) => ({ W: "win", D: "draw", L: "loss" })[r.outcome] ?? "")
    .join(" ")}`;

  return (
    <svg
      className="sparkline"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-label={label}
      role="img"
    >
      <polyline fill="none" stroke="#4D8BFF" strokeWidth={2} points={points} />
      {coords.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={2.5} fill={DOT_COLOR[ordered[i].outcome] ?? "#6B7A9E"} />
      ))}
    </svg>
  );
}
