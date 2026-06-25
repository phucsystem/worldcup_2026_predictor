import Link from "next/link";
import { getAllResults } from "@/lib/api";
import { resultRowsFromResults } from "@/lib/results";
import ResultsWidget from "@/components/results-widget";
import EmptyState from "@/components/empty-state";

export const dynamic = "force-dynamic";

export const metadata: import("next").Metadata = {
  title: "Results",
  description:
    "Every completed 2026 World Cup result with scores, groups and how each match compared to our pre-match forecast.",
  alternates: { canonical: "/results" },
};

export default async function ResultsPage() {
  const rows = resultRowsFromResults(await getAllResults());

  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <div className="flex items-baseline justify-between mb-8 flex-wrap gap-2">
        <h1 className="text-2xl font-bold" style={{ color: "#FFFFFF" }}>
          All Results
        </h1>
        <Link
          href="/"
          className="text-sm font-medium hover:underline"
          style={{ color: "#2D6BF6" }}
        >
          ← Home
        </Link>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          message="No results yet."
          subtext="Match results appear here once games kick off."
        />
      ) : (
        <ResultsWidget rows={rows} />
      )}
    </div>
  );
}
