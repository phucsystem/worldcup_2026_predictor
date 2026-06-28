import { getKnockout } from "@/lib/api";
import KnockoutBracket from "@/components/knockout-bracket";
import { TimezoneNote } from "@/components/local-time";

export const dynamic = "force-dynamic";

export const metadata: import("next").Metadata = {
  title: "Knockout Bracket",
  description:
    "The 2026 World Cup knockout bracket — Round of 32 through the Final, with live scores and results shown in your local time.",
  alternates: { canonical: "/knockout" },
};

export default async function KnockoutPage() {
  const knockout = await getKnockout();

  return (
    <div className="px-6 py-8" style={{ maxWidth: "1120px", margin: "0 auto" }}>
      <div className="flex items-baseline justify-between gap-4 flex-wrap mb-6">
        <h1
          className="font-extrabold"
          style={{ color: "#FFFFFF", fontSize: "clamp(1.75rem, 3vw, 2.25rem)" }}
        >
          Knockout
        </h1>
        <TimezoneNote className="text-xs" style={{ color: "#6B7A9E" }} />
      </div>

      <KnockoutBracket bracket={knockout} />
    </div>
  );
}
