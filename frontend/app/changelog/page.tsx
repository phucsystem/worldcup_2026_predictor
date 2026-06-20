import { readFile } from "node:fs/promises";
import path from "node:path";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import EmptyState from "@/components/empty-state";

export const dynamic = "force-dynamic";

async function loadChangelog(): Promise<string | null> {
  // Lives in public/ so it ships in the Next standalone Docker image (the
  // Dockerfile copies public/) and resolves under process.cwd() in dev too.
  try {
    return await readFile(path.join(process.cwd(), "public", "CHANGELOG.md"), "utf8");
  } catch {
    return null;
  }
}

export default async function ChangelogPage() {
  const markdown = await loadChangelog();

  return (
    <div className="px-6 py-8" style={{ maxWidth: "760px", margin: "0 auto" }}>
      <h1 className="font-extrabold mb-6" style={{ color: "#FFFFFF", fontSize: "clamp(1.75rem, 3vw, 2.25rem)" }}>
        Changelog
      </h1>

      {markdown ? (
        <div className="prose-brief" style={{ lineHeight: 1.6, fontSize: "16px" }}>
          <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{markdown}</ReactMarkdown>
        </div>
      ) : (
        <EmptyState message="Changelog is temporarily unavailable" />
      )}
    </div>
  );
}
