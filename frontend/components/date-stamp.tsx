interface Props {
  date: string; // YYYY-MM-DD
  fresh?: boolean;
}

export default function DateStamp({ date, fresh = false }: Props) {
  const display = new Date(date + "T00:00:00").toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).toUpperCase();

  return (
    <p
      className="text-xs font-semibold uppercase tracking-widest"
      style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}
      aria-label={fresh ? `Today, ${display}` : display}
    >
      {fresh ? `Today · ${display} · Updated 7:00 AM AEST` : display}
    </p>
  );
}
