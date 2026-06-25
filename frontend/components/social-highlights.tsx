import type { SocialHighlight } from "@/lib/api";
import { kickoffDayLabel } from "@/lib/time";

interface Props {
  highlights: SocialHighlight[];
}

const SOURCE_LABELS: Record<string, string> = {
  reddit: "Reddit",
  bluesky: "Bluesky",
  x: "X",
  news: "News",
};

function isHttpUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

// "What people are saying" — curated public discussion (Reddit/X) and news
// reporting about an upcoming match. Presentational only; all content is
// auto-curated (lib/api FixtureDetail.social_highlights). Renders nothing when
// there are no highlights, so there is never an empty shell. Distinct from the
// model forecast both visually and in labelling — opinion/reporting, not a prediction.
export default function SocialHighlights({ highlights }: Props) {
  if (highlights.length === 0) return null;
  return (
    <section className="social-highlights" aria-label="What people are saying before kickoff">
      <div className="sh-head">
        <h2 className="sh-title">What people are saying · before kickoff</h2>
        <span className="sh-tag">Discussion &amp; news · auto-curated</span>
      </div>
      <ul className="sh-list">
        {highlights.map((h, i) => {
          const sourceLabel = SOURCE_LABELS[h.source] ?? h.source;
          const meta = (
            <span className="sh-meta">
              <span className={`sh-source ${h.source}`}>{sourceLabel}</span>
              <span className="sh-author">{h.author}</span>
              {h.posted_at ? <span className="sh-date">{kickoffDayLabel(h.posted_at)}</span> : null}
            </span>
          );
          return (
            <li className="sh-item" key={`${h.url}-${i}`}>
              <p className="sh-text">{h.text}</p>
              {h.why ? <span className="sh-why">{h.why}</span> : null}
              {isHttpUrl(h.url) ? (
                <a
                  className="sh-link"
                  href={h.url}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                >
                  {meta}
                  <span className="sh-viewsrc">View source →</span>
                </a>
              ) : (
                meta
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
