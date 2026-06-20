interface Props {
  lines?: number;
}

// Loading placeholder mirroring the prototype `.skeleton-card`/`.skeleton-line`.
// Shimmer animation is gated by prefers-reduced-motion in globals.css.
export default function SkeletonCard({ lines = 3 }: Props) {
  return (
    <div className="skeleton-card" aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-line"
          style={{ width: i === lines - 1 ? "60%" : "100%" }}
        />
      ))}
    </div>
  );
}
