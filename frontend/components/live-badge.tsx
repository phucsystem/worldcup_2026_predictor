/** Small "LIVE" pill. Text label (not color-only) so it never relies on color
 * alone to convey state. */
export default function LiveBadge() {
  return (
    <span
      className="inline-flex items-center gap-1 text-xs font-bold uppercase px-2 py-0.5"
      style={{ backgroundColor: "rgba(255,90,90,0.15)", color: "#FF5A5A", borderRadius: "999px", letterSpacing: "0.04em" }}
    >
      <span aria-hidden="true" style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#FF5A5A", display: "inline-block" }} />
      Live
    </span>
  );
}
