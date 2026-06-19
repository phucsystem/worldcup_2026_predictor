import { notFound } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import { getBrief } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function BriefPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const brief = await getBrief(date);

  if (!brief) notFound();

  const displayDate = new Date(date + "T00:00:00").toLocaleDateString("en-AU", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const generatedAt =
    brief.created_at
      ? new Date(brief.created_at).toLocaleString("en-AU", {
          timeZone: "Australia/Melbourne",
          dateStyle: "medium",
          timeStyle: "short",
        })
      : null;

  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <nav aria-label="Breadcrumb">
        <Link
          href="/"
          className="text-sm mb-6 inline-block hover:text-white transition-colors focus-visible:rounded"
          style={{ color: "#6B7A9E" }}
        >
          ← Back to Today
        </Link>
      </nav>

      <p
        className="text-xs font-semibold uppercase tracking-widest mb-3"
        style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}
      >
        {displayDate} · AEST
      </p>

      <h1
        className="font-extrabold mb-4"
        style={{ color: "#FFFFFF", lineHeight: 1.15, fontSize: "clamp(2rem, 3vw, 2.5rem)" }}
      >
        {brief.title ?? "Daily Brief"}
      </h1>

      {brief.summary && (
        <p className="text-lg mb-8" style={{ color: "#A9B6D4", lineHeight: 1.5 }}>
          {brief.summary}
        </p>
      )}

      <hr style={{ borderColor: "#1E3157", marginBottom: "2rem" }} />

      {brief.body_md && (
        <div className="prose-brief" style={{ lineHeight: 1.6, fontSize: "16px" }}>
          <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{brief.body_md}</ReactMarkdown>
        </div>
      )}

      <hr style={{ borderColor: "#1E3157", marginTop: "3rem", marginBottom: "1rem" }} />

      <footer>
        <p className="text-xs" style={{ color: "#6B7A9E" }}>
          {brief.model_used && <span>Model: {brief.model_used}{generatedAt ? " · " : ""}</span>}
          {generatedAt && <span>Generated: {generatedAt} AEST</span>}
        </p>
      </footer>
    </div>
  );
}
