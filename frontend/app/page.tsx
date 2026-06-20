import Link from "next/link";
import { listBriefs, getLatestBrief, getUpcomingFixtures, getStars } from "@/lib/api";
import { HeroBriefCard, CompactBriefCard } from "@/components/brief-card";
import FixtureRow from "@/components/fixture-row";
import StarCard from "@/components/star-card";
import EmptyState from "@/components/empty-state";

export const dynamic = "force-dynamic";

const TODAY = new Date()
  .toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" })
  .toUpperCase();

export default async function HomePage() {
  const [latest, briefs, upcoming, stars] = await Promise.all([
    getLatestBrief(),
    listBriefs(),
    getUpcomingFixtures(),
    getStars(),
  ]);
  const earlier = briefs.filter((b) => b.date !== latest?.date).slice(0, 9);
  const upNext = upcoming.up_next;
  const topStars = stars.slice(0, 6);

  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <h1 className="sr-only">WC26 Intelligence — Daily Brief</h1>

      <p
        className="text-xs font-semibold uppercase tracking-widest mb-4"
        style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}
        aria-label={`Today, ${TODAY}, Updated 7:00 AM AEST`}
      >
        Today · {TODAY} · Updated 7:00 AM AEST
      </p>

      {latest ? (
        <div className="mb-10">
          <HeroBriefCard brief={latest} />
        </div>
      ) : (
        <div className="mb-10">
          <EmptyState
            message="Today's brief publishes at 7:00 AM AEST"
            subtext="Check back after 7:00 AM Australia/Melbourne"
          />
        </div>
      )}

      {upNext && (
        <section aria-label="Up next" className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}>
            Up next
          </p>
          <FixtureRow fixture={upNext} showCountdown />
        </section>
      )}

      {topStars.length > 0 && (
        <section aria-label="Stars to watch" className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}>
            Stars to watch
          </p>
          <div className="flex gap-3 overflow-x-auto pb-2" style={{ WebkitOverflowScrolling: "touch" }}>
            {topStars.map((s) => (
              <StarCard key={s.player_id} player={s} />
            ))}
          </div>
        </section>
      )}

      {earlier.length > 0 && (
        <section aria-label="Earlier briefs">
          <p
            className="text-xs font-semibold uppercase tracking-widest mb-4"
            style={{ color: "#6B7A9E", letterSpacing: "0.08em" }}
          >
            Earlier
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {earlier.map((b) => (
              <CompactBriefCard key={b.date} brief={b} />
            ))}
          </div>
          <div className="mt-6 text-center">
            <Link
              href="/archive"
              className="text-sm font-medium hover:underline"
              style={{ color: "#2D6BF6" }}
            >
              View archive →
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
