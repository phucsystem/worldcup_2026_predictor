import { readFile } from "node:fs/promises";
import path from "node:path";
import { Fragment, type ReactNode } from "react";
import EmptyState from "@/components/empty-state";

export const dynamic = "force-dynamic";

type Change = { tag: string; text: string };
type VersionEntry = { version: string; date: string; changes: Change[] };
type ParsedChangelog = { deck: string | null; versions: VersionEntry[]; roadmap: string[] };

const TAG_CLASS: Record<string, string> = {
  added: "cl-added",
  improved: "cl-improved",
  fixed: "cl-fixed",
  milestone: "cl-milestone",
};

async function loadChangelog(): Promise<string | null> {
  // Lives in public/ so it ships in the Next standalone Docker image (the
  // Dockerfile copies public/) and resolves under process.cwd() in dev too.
  try {
    return await readFile(path.join(process.cwd(), "public", "CHANGELOG.md"), "utf8");
  } catch {
    return null;
  }
}

function parseChangelog(md: string): ParsedChangelog {
  let deck: string | null = null;
  const versions: VersionEntry[] = [];
  const roadmap: string[] = [];
  let mode: "none" | "version" | "roadmap" = "none";
  let current: VersionEntry | null = null;
  let seenTitle = false;

  for (const raw of md.split("\n")) {
    const line = raw.trim();
    if (!line) continue;

    if (line.startsWith("# ")) {
      seenTitle = true;
      continue;
    }

    const heading = line.match(/^##\s+(.+)$/);
    if (heading) {
      const title = heading[1].trim();
      if (/^on the roadmap/i.test(title)) {
        mode = "roadmap";
        current = null;
      } else {
        const [version, ...rest] = title.split(/\s+—\s+/);
        current = { version: version.trim(), date: rest.join(" — ").trim(), changes: [] };
        versions.push(current);
        mode = "version";
      }
      continue;
    }

    if (line.startsWith("- ")) {
      const item = line.slice(2).trim();
      if (mode === "roadmap") {
        roadmap.push(item.replace(/\.$/, ""));
      } else if (mode === "version" && current) {
        const tagged = item.match(/^\*\*(.+?)\*\*\s+—\s+(.+)$/);
        if (tagged) current.changes.push({ tag: tagged[1].trim(), text: tagged[2].trim() });
        else current.changes.push({ tag: "", text: item });
      }
      continue;
    }

    if (seenTitle && mode === "none" && !deck) deck = line;
  }

  return { deck, versions, roadmap };
}

// Render the limited inline markdown the changelog uses: **bold** and `code`.
function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const token = /\*\*(.+?)\*\*|`([^`]+?)`/g;
  let last = 0;
  let key = 0;
  let m: RegExpExecArray | null;
  while ((m = token.exec(text)) !== null) {
    if (m.index > last) nodes.push(<Fragment key={key++}>{text.slice(last, m.index)}</Fragment>);
    if (m[1] !== undefined) nodes.push(<strong key={key++}>{m[1]}</strong>);
    else nodes.push(<code key={key++}>{m[2]}</code>);
    last = token.lastIndex;
  }
  if (last < text.length) nodes.push(<Fragment key={key++}>{text.slice(last)}</Fragment>);
  return nodes;
}

export const metadata: import("next").Metadata = {
  title: "Changelog",
  description: "What's new in WC26 Intelligence — recent features, fixes and updates.",
  alternates: { canonical: "/changelog" },
};

export default async function ChangelogPage() {
  const markdown = await loadChangelog();

  if (!markdown) {
    return (
      <main className="main-content reading">
        <h1 className="page-title">Changelog</h1>
        <div className="mt-6">
          <EmptyState message="Changelog is temporarily unavailable" />
        </div>
      </main>
    );
  }

  const { deck, versions, roadmap } = parseChangelog(markdown);

  return (
    <main className="main-content reading">
      <div style={{ marginBottom: "var(--space-6)" }}>
        <h1 className="page-title">Changelog</h1>
        {deck && (
          <p className="summary-deck" style={{ marginTop: "var(--space-2)" }}>
            {deck}
          </p>
        )}
      </div>

      <div className="changelog">
        {versions.map((entry, i) => (
          <article key={entry.version} className={i === 0 ? "changelog-entry latest" : "changelog-entry"}>
            <div className="cl-head">
              <span className="cl-version">{entry.version}</span>
              {entry.date && <span className="cl-date">{entry.date}</span>}
              {i === 0 && <span className="cl-shipped-pill">Latest</span>}
            </div>
            <div className="cl-card">
              {entry.changes.map((c, j) => (
                <div key={j} className="cl-change">
                  {c.tag && (
                    <span className={`cl-tag ${TAG_CLASS[c.tag.toLowerCase()] ?? ""}`.trim()}>
                      {c.tag}
                    </span>
                  )}
                  <span className="cl-change-text">{renderInline(c.text)}</span>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>

      {roadmap.length > 0 && (
        <>
          <h2 className="section-title">On the roadmap</h2>
          <div className="roadmap-card">
            {roadmap.map((item, i) => (
              <div key={i} className="roadmap-item">
                <span className="rm-box" />
                {renderInline(item)}
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
