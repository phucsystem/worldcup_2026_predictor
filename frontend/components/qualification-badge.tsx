export type QualificationStatus = "qualified" | "contention" | "eliminated" | null;

interface Props {
  status: QualificationStatus;
}

const CONFIG = {
  qualified: {
    icon: "●",
    label: "Q",
    color: "#2BD37E",
    ariaLabel: "Qualified",
  },
  contention: {
    icon: "○",
    label: "C",
    color: "#F4B740",
    ariaLabel: "In contention",
  },
  eliminated: {
    icon: "✕",
    label: "E",
    color: "#FF5A5A",
    ariaLabel: "Eliminated",
  },
} as const;

export default function QualificationBadge({ status }: Props) {
  if (!status) return null;
  const cfg = CONFIG[status];
  return (
    <span
      aria-label={cfg.ariaLabel}
      title={cfg.ariaLabel}
      style={{ color: cfg.color, fontSize: "0.75rem" }}
    >
      {cfg.icon}
      <span className="sr-only"> {cfg.ariaLabel}</span>
    </span>
  );
}
