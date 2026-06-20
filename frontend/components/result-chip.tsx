import type { RecentResult } from "@/lib/api";
import { resultsToChips } from "@/lib/results";

interface Props {
  results: RecentResult[];
  className?: string;
}

// Renders recent finished matches as `W BRA 3–1 SER` pill chips.
// Graceful degrade: nothing when there are no results.
export default function ResultChips({ results, className }: Props) {
  const chips = resultsToChips(results);
  if (chips.length === 0) return null;
  return (
    <div className={`chip-row${className ? ` ${className}` : ""}`}>
      {chips.map((c) => (
        <span key={c.key} className={`result-chip ${c.variant}`}>
          <span className="rc-letter">{c.letter}</span> {c.label}
        </span>
      ))}
    </div>
  );
}
