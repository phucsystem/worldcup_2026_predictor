// Pure data→view helpers for the form Sparkline. No DOM, unit-tested.

// Outcome → vertical value. Win sits highest, loss lowest.
export const OUTCOME_VALUE: Record<string, number> = { W: 2, D: 1, L: 0 };

const PAD_X = 5;
const PAD_Y = 4;
const V_MIN = 0;
const V_MAX = 2;

function round(n: number): number {
  return Math.round(n * 100) / 100;
}

/**
 * Build an SVG polyline `points` string from a fixed-domain value series
 * (W=2 / D=1 / L=0). Values map against the fixed [0,2] domain — a lone win
 * always sits at the top regardless of the rest — so the line shape is
 * comparable across teams. Returns "" for < 2 points (nothing to draw).
 */
export function sparklinePath(values: number[], w = 70, h = 20): string {
  if (values.length < 2) return "";
  const n = values.length;
  const innerW = w - 2 * PAD_X;
  const innerH = h - 2 * PAD_Y;
  const span = V_MAX - V_MIN;
  return values
    .map((v, i) => {
      const clamped = Math.max(V_MIN, Math.min(V_MAX, v));
      const x = PAD_X + (i * innerW) / (n - 1);
      // higher value → higher on the chart → smaller y
      const y = PAD_Y + (1 - (clamped - V_MIN) / span) * innerH;
      return `${round(x)},${round(y)}`;
    })
    .join(" ");
}
