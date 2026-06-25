import { getUpcomingFixtures, getKnockout } from "@/lib/api";
import FixturesView from "@/components/fixtures-view";
import { TimezoneNote } from "@/components/local-time";

export const dynamic = "force-dynamic";

export const metadata: import("next").Metadata = {
  title: "Fixtures & Schedule",
  description:
    "The full 2026 World Cup fixture list and knockout bracket — upcoming kickoffs shown in your local time.",
  alternates: { canonical: "/fixtures" },
};

export default async function FixturesPage() {
  const [upcoming, knockout] = await Promise.all([getUpcomingFixtures(), getKnockout()]);

  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <div className="flex items-baseline justify-between gap-4 flex-wrap mb-6">
        <h1 className="font-extrabold" style={{ color: "#FFFFFF", fontSize: "clamp(1.75rem, 3vw, 2.25rem)" }}>
          Fixtures
        </h1>
        <TimezoneNote className="text-xs" style={{ color: "#6B7A9E" }} />
      </div>

      <FixturesView upcoming={upcoming} knockout={knockout} />
    </div>
  );
}
