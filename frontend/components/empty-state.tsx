interface Props {
  message?: string;
  subtext?: string;
}

export default function EmptyState({
  message = "Today's brief publishes at 7:00 AM AEST",
  subtext,
}: Props) {
  return (
    <div
      className="p-8 rounded-xl border text-center"
      style={{
        backgroundColor: "#0A1B3D",
        borderColor: "#1E3157",
        borderRadius: "12px",
      }}
      role="status"
    >
      <p className="text-lg" style={{ color: "#A9B6D4" }}>
        {message}
      </p>
      {subtext && (
        <p className="text-sm mt-2" style={{ color: "#6B7A9E" }}>
          {subtext}
        </p>
      )}
    </div>
  );
}
