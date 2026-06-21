import { flagSvg } from "@/lib/flags";

interface Props {
  home: string | null;
  away: string | null;
}

// Faded two-team flag backdrop for a match hero: home flag fills the left, away
// the right, with a dark tint on top for readability. Mirrors the prototype's
// data-flag-bg layer. Renders nothing if neither team has a built flag.
// The parent .next-match must carry data-flag-bg so its decorative ball hides.
export default function FlagBackdrop({ home, away }: Props) {
  const homeSvg = flagSvg(home);
  const awaySvg = flagSvg(away);
  if (!homeSvg && !awaySvg) return null;
  return (
    <div className="flag-bg" aria-hidden="true">
      {homeSvg ? (
        <div className="flag-bg-half home">
          <svg viewBox="0 0 30 20" preserveAspectRatio="xMidYMid slice" dangerouslySetInnerHTML={{ __html: homeSvg }} />
        </div>
      ) : null}
      {awaySvg ? (
        <div className="flag-bg-half away">
          <svg viewBox="0 0 30 20" preserveAspectRatio="xMidYMid slice" dangerouslySetInnerHTML={{ __html: awaySvg }} />
        </div>
      ) : null}
      <div className="flag-bg-tint" />
    </div>
  );
}
