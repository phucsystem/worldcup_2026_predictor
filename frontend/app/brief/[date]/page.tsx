import { notFound } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import { getBrief } from "@/lib/api";
import BriefHeroArt from "@/components/brief-hero-art";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ date: string }>;
}): Promise<import("next").Metadata> {
  const { date } = await params;
  const brief = await getBrief(date);
  if (!brief) return {};
  const title = brief.title ?? `World Cup 2026 Daily Brief · ${date}`;
  const description =
    brief.summary ?? `World Cup 2026 intelligence brief for ${date} — storylines, standings and forecasts.`;
  return {
    title,
    description,
    alternates: { canonical: `/brief/${date}` },
    openGraph: { title, description, type: "article" },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function BriefPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const brief = await getBrief(date);

  if (!brief) notFound();

  const displayDate = new Date(date + "T00:00:00").toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  const generatedAt = brief.created_at
    ? new Date(brief.created_at).toLocaleString("en-AU", {
        timeZone: "Australia/Melbourne",
        dateStyle: "medium",
        timeStyle: "short",
      })
    : null;

  return (
    <div className="brief-page">
      <div className="brief-sheet">
        <div className="brief-sheet-head">
          <Link className="back-link" href="/">
            ‹ Back to Today
          </Link>
          <span className="meta-label">{displayDate} · AEST</span>
        </div>

        <section className="brief-hero" aria-label={brief.title ?? "Daily Brief"}>
          <div className="bh-art" aria-hidden="true">
            <BriefHeroArt />
          </div>
          <div className="bh-scrim" aria-hidden="true" />
          <div className="bh-content">
            <span className="bh-eyebrow">
              <span className="dot" /> Daily Brief
            </span>
            <h1 className="display-headline">{brief.title ?? "Daily Brief"}</h1>
            {brief.summary && <p className="summary-deck">{brief.summary}</p>}
          </div>
        </section>

        {brief.body_md && (
          <article className="prose-brief">
            <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{brief.body_md}</ReactMarkdown>
          </article>
        )}

        {(brief.model_used || generatedAt) && (
          <>
            <hr className="brief-divider" />
            <div className="provenance">
              {brief.model_used && <span>model: {brief.model_used}</span>}
              {brief.model_used && generatedAt && <span>·</span>}
              {generatedAt && <span>generated {generatedAt} AEST</span>}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
