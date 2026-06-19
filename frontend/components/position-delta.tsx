interface Props {
  position: number | null;
  prevPosition: number | null;
}

export default function PositionDelta({ position, prevPosition }: Props) {
  if (position == null || prevPosition == null || prevPosition === 0) {
    return (
      <span aria-label="no change" style={{ color: "#6B7A9E" }}>
        –
      </span>
    );
  }
  if (prevPosition > position) {
    return (
      <span aria-label="moved up" style={{ color: "#2BD37E" }}>
        ▲
      </span>
    );
  }
  if (prevPosition < position) {
    return (
      <span aria-label="moved down" style={{ color: "#FF5A5A" }}>
        ▼
      </span>
    );
  }
  return (
    <span aria-label="no change" style={{ color: "#6B7A9E" }}>
      –
    </span>
  );
}
