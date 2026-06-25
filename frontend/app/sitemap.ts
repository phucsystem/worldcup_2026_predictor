import type { MetadataRoute } from "next";
import { SITE } from "@/lib/site";
import { listBriefs, getAllResults, getUpcomingFixtures } from "@/lib/api";

const STATIC_PATHS = ["", "/standings", "/results", "/fixtures", "/archive", "/changelog"];

// Dynamic content is best-effort: a failed fetch must not break sitemap generation,
// it just yields a smaller sitemap that the next crawl will fill in.
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const url = (path: string) => `${SITE.url}${path}`;

  const entries: MetadataRoute.Sitemap = STATIC_PATHS.map((path) => ({
    url: url(path),
    changeFrequency: "daily",
    priority: path === "" ? 1 : 0.7,
  }));

  const [briefs, results, upcoming] = await Promise.all([
    listBriefs().catch(() => []),
    getAllResults().catch(() => []),
    getUpcomingFixtures().catch(() => null),
  ]);

  for (const brief of briefs) {
    entries.push({ url: url(`/brief/${brief.date}`), changeFrequency: "monthly", priority: 0.5 });
  }

  const fixtureIds = new Set<number>();
  for (const r of results) if (r.fixture_id != null) fixtureIds.add(r.fixture_id);
  for (const day of upcoming?.days ?? [])
    for (const f of day.fixtures) fixtureIds.add(f.fixture_id);

  for (const id of fixtureIds) {
    entries.push({ url: url(`/match/${id}`), changeFrequency: "daily", priority: 0.6 });
  }

  return entries;
}
