import { readFile } from "node:fs/promises";
import { join } from "node:path";
import type { ReactNode } from "react";
import type { FixtureDetail } from "@/lib/api";
import { flagSvg } from "@/lib/flags";
import { goalscorers } from "@/lib/match";
import { matchState } from "@/lib/match";
import { forecastSegments } from "@/lib/banner";
import { SITE } from "@/lib/site";

// Shared render for the share/OG image. Satori (next/og) only supports flexbox
// and a CSS subset — every multi-child node carries display:flex, and the live
// DOM's gradient/blur backdrop is approximated with a flat tint. Consumed by the
// share-image route handler and the match page's opengraph-image.

const SIZE = { width: 1200, height: 630 } as const;
const GREEN = "#2BD37E";
const MUTED = "#A9B6D4";

const FINISHED_LABEL: Record<string, string> = {
  FT: "Full Time",
  AET: "After Extra Time",
  PEN: "Penalties",
};

const assetPath = (file: string) => join(process.cwd(), "assets", file);

export async function loadShareFonts() {
  const [regular, bold, extra] = await Promise.all([
    readFile(assetPath("Inter-Regular.ttf")),
    readFile(assetPath("Inter-Bold.ttf")),
    readFile(assetPath("Inter-ExtraBold.ttf")),
  ]);
  return [
    { name: "Inter", data: regular, weight: 400 as const, style: "normal" as const },
    { name: "Inter", data: bold, weight: 700 as const, style: "normal" as const },
    { name: "Inter", data: extra, weight: 800 as const, style: "normal" as const },
  ];
}

function hasKickedOff(kickoffUtc: string | null): boolean {
  if (!kickoffUtc) return false;
  const t = Date.parse(kickoffUtc);
  return Number.isFinite(t) && t <= Date.now();
}

export function isLiveFixture(fixture: FixtureDetail): boolean {
  const state = matchState(fixture.status);
  if (state === "live") return true;
  if (state === "finished") return false;
  // Status hasn't flipped to live yet (poller lag) but kickoff has passed — treat
  // as live so the share image shows the score layout, not an upcoming "VS" card.
  return hasKickedOff(fixture.kickoff_utc);
}

// Which banner layout to draw. Only a genuinely upcoming match (status not
// live/finished AND kickoff still in the future) gets the "VS" preview; a
// kicked-off match renders the score layout even if its status lags at NS.
export function shareBannerVariant(fixture: FixtureDetail): "preview" | "result" {
  return matchState(fixture.status) === "preview" && !isLiveFixture(fixture)
    ? "preview"
    : "result";
}

// Strict positive-integer id — rejects "5.7", "abc", " 5", "0x10", "1e3" so the
// share/OG routes never forward a bogus value to the backend.
export function parseFixtureId(raw: string): number | null {
  const id = Number.parseInt(raw, 10);
  return Number.isInteger(id) && id > 0 && String(id) === raw ? id : null;
}

function statusLabel(fixture: FixtureDetail): string {
  if (isLiveFixture(fixture)) {
    return fixture.elapsed != null ? `LIVE ${fixture.elapsed}'` : "LIVE";
  }
  const code = (fixture.status ?? "").toUpperCase();
  return FINISHED_LABEL[code] ?? "Full Time";
}

function initials(team: string | null): string {
  if (!team) return "?";
  const parts = team.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function flagDataUri(team: string | null): string | null {
  const inner = flagSvg(team);
  if (!inner) return null;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20" preserveAspectRatio="xMidYMid slice">${inner}</svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}

function goalMark(detail: string | null): string {
  const d = (detail ?? "").toLowerCase();
  if (d === "penalty") return " (pen)";
  if (d === "own goal") return " (o.g.)";
  return "";
}

function scorerLines(fixture: FixtureDetail): string[] {
  return goalscorers(fixture.events).map((e) => {
    const mins = e.goals.map((g) => `${g.minute}'${goalMark(g.detail)}`).join(", ");
    return `⚽ ${e.player ?? "—"} ${mins}`.trim();
  });
}

function kickoffText(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const tz = "Australia/Melbourne";
  const date = new Intl.DateTimeFormat("en-AU", {
    timeZone: tz,
    weekday: "short",
    day: "numeric",
    month: "long",
  }).format(d);
  const time = new Intl.DateTimeFormat("en-AU", {
    timeZone: tz,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(d);
  const zone =
    new Intl.DateTimeFormat("en-AU", { timeZone: tz, hour: "2-digit", timeZoneName: "short" })
      .formatToParts(d)
      .find((p) => p.type === "timeZoneName")?.value ?? "";
  return `${date} · ${time} ${zone}`.trim();
}

const ACCENT = "#4D8BFF";

// Soccer-ball mark from components/brand-logo.tsx, as pure SVG shapes only — no
// <text>, since Satori hands nested SVG to resvg which has no font for it (the
// "WC26 INTELLIGENCE" wordmark is rendered with Satori-native text instead).
const BALL_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-16 -16 32 32" width="44" height="44"><circle r="14.5" fill="#FFFFFF" stroke="#0A1B3D" stroke-width="1.4"/><polygon points="0,-7 6.66,-2.16 4.11,5.66 -4.11,5.66 -6.66,-2.16" fill="#0A1B3D"/><g stroke="#0A1B3D" stroke-width="1.4" stroke-linecap="round"><line x1="0" y1="-7" x2="0" y2="-14.5"/><line x1="6.66" y1="-2.16" x2="13.8" y2="-4.48"/><line x1="4.11" y1="5.66" x2="8.52" y2="11.73"/><line x1="-4.11" y1="5.66" x2="-8.52" y2="11.73"/><line x1="-6.66" y1="-2.16" x2="-13.8" y2="-4.48"/></g></svg>`;
const BALL_URI = `data:image/svg+xml;base64,${Buffer.from(BALL_SVG).toString("base64")}`;

// Brand lockup built from Satori-native text so the wordmark always renders.
function brandLockup(size: "sm" | "lg") {
  const ball = size === "lg" ? 64 : 44;
  const word = size === "lg" ? 44 : 30;
  const sub = size === "lg" ? 14 : 10;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <img src={BALL_URI} alt="" width={ball} height={ball} style={{ width: ball, height: ball }} />
      <div style={{ display: "flex", flexDirection: "column" }}>
        <div style={{ display: "flex", fontSize: word, fontWeight: 800, letterSpacing: -1, lineHeight: 1 }}>
          <span style={{ color: "#fff" }}>{SITE.wordmark.primary}</span>
          <span style={{ color: ACCENT }}>{SITE.wordmark.accent}</span>
        </div>
        <div style={{ display: "flex", fontSize: sub, fontWeight: 600, letterSpacing: 4, color: MUTED, marginTop: 4 }}>
          {SITE.wordmark.sub}
        </div>
      </div>
    </div>
  );
}

type SideOutcome = "win" | "lose" | "draw";

function crest(logo: string | null, team: string | null) {
  if (logo) {
    return (
      <img
        src={logo}
        alt=""
        width={104}
        height={104}
        style={{ width: 104, height: 104, objectFit: "contain", borderRadius: 12 }}
      />
    );
  }
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: 104,
        height: 104,
        borderRadius: 12,
        backgroundColor: "#13294F",
        color: MUTED,
        fontSize: 40,
        fontWeight: 800,
      }}
    >
      {initials(team)}
    </div>
  );
}

function teamSide(team: string | null, logo: string | null, outcome: SideOutcome) {
  const dim = outcome === "lose";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
        width: 340,
        opacity: dim ? 0.55 : 1,
      }}
    >
      {crest(logo, team)}
      <div style={{ display: "flex", fontSize: 38, fontWeight: 700, textAlign: "center" }}>
        {team ?? "TBD"}
      </div>
      {outcome === "win" ? (
        <div
          style={{
            display: "flex",
            fontSize: 22,
            fontWeight: 800,
            color: GREEN,
            backgroundColor: "rgba(43,211,126,0.16)",
            padding: "4px 14px",
            borderRadius: 999,
          }}
        >
          W
        </div>
      ) : null}
    </div>
  );
}

// Faded dual-flag backdrop shared by every share-image variant.
function shareBackdrop(homeFlag: string | null, awayFlag: string | null) {
  return (
    <div style={{ display: "flex", position: "absolute", top: 0, left: 0, right: 0, bottom: 0 }}>
      {homeFlag ? (
        <img
          src={homeFlag}
          alt=""
          width={620}
          height={630}
          style={{ position: "absolute", left: 0, top: 0, width: 620, height: 630, objectFit: "cover", opacity: 0.16 }}
        />
      ) : null}
      {awayFlag ? (
        <img
          src={awayFlag}
          alt=""
          width={620}
          height={630}
          style={{ position: "absolute", right: 0, top: 0, width: 620, height: 630, objectFit: "cover", opacity: 0.16 }}
        />
      ) : null}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: "linear-gradient(180deg, rgba(8,18,42,0.45) 0%, rgba(8,18,42,0.78) 100%)",
        }}
      />
    </div>
  );
}

// Brand + domain footer shared by every share-image variant.
function shareFooter() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 48px 40px" }}>
      {brandLockup("sm")}
      <div style={{ display: "flex", fontSize: 24, fontWeight: 600, color: MUTED }}>{SITE.domain}</div>
    </div>
  );
}

// Outer 1200×630 frame: gradient base + flag backdrop + center content + footer.
function shareFrame(homeFlag: string | null, awayFlag: string | null, children: ReactNode) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: SIZE.width,
        height: SIZE.height,
        position: "relative",
        fontFamily: "Inter",
        color: "#fff",
        backgroundColor: "#0a1430",
        backgroundImage: "linear-gradient(135deg, #0a1430 0%, #122a52 100%)",
      }}
    >
      {shareBackdrop(homeFlag, awayFlag)}
      {children}
      {shareFooter()}
    </div>
  );
}

function statusPill(label: string, live: boolean) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        fontSize: 24,
        fontWeight: 700,
        letterSpacing: 1,
        textTransform: "uppercase",
        color: live ? GREEN : MUTED,
        backgroundColor: live ? "rgba(43,211,126,0.14)" : "rgba(107,122,158,0.16)",
        border: `1px solid ${live ? "rgba(43,211,126,0.4)" : "rgba(107,122,158,0.4)"}`,
        padding: "10px 22px",
        borderRadius: 999,
        marginBottom: 36,
      }}
    >
      <div style={{ display: "flex", width: 12, height: 12, borderRadius: 999, backgroundColor: live ? GREEN : MUTED }} />
      {label}
    </div>
  );
}

// Upcoming variant — VS (no score) + win-probability bar + kickoff. Mirrors the
// on-page preview hero so the copied image matches what the user sees.
function previewContent(fixture: FixtureDetail, context: string) {
  const seg = forecastSegments(fixture.forecast);
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        padding: "56px 64px",
      }}
    >
      {statusPill(`Preview${context ? ` · ${context}` : ""}`, false)}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 36 }}>
        {teamSide(fixture.home_team, fixture.home_logo, "draw")}
        <div style={{ display: "flex", fontSize: 88, fontWeight: 800, color: "rgba(255,255,255,0.6)" }}>VS</div>
        {teamSide(fixture.away_team, fixture.away_logo, "draw")}
      </div>

      {seg ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, marginTop: 36 }}>
          <div style={{ display: "flex", fontSize: 20, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", color: MUTED }}>
            Win probability · experimental
          </div>
          <div style={{ display: "flex", width: 760, height: 56, borderRadius: 999, overflow: "hidden" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: `${seg.homePct}%`, backgroundColor: ACCENT, color: "#04122E", fontSize: 28, fontWeight: 800 }}>
              {seg.homePct}%
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: `${seg.drawPct}%`, backgroundColor: "#F4B740", color: "#2A1E00", fontSize: 28, fontWeight: 800 }}>
              {seg.drawPct}%
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: `${seg.awayPct}%`, backgroundColor: MUTED, color: "#fff", fontSize: 28, fontWeight: 800 }}>
              {seg.awayPct}%
            </div>
          </div>
        </div>
      ) : null}

      <div style={{ display: "flex", fontSize: 24, color: MUTED, marginTop: 30 }}>
        {kickoffText(fixture.kickoff_utc)}
      </div>
    </div>
  );
}

// Live / finished variant — score with win/lose emphasis + scorers + kickoff.
function resultContent(fixture: FixtureDetail, context: string) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const homeOutcome: SideOutcome = hs > as ? "win" : as > hs ? "lose" : "draw";
  const awayOutcome: SideOutcome = as > hs ? "win" : hs > as ? "lose" : "draw";
  const scorers = scorerLines(fixture);
  const live = isLiveFixture(fixture);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        padding: "56px 64px",
      }}
    >
      {statusPill(`${statusLabel(fixture)}${context ? ` · ${context}` : ""}`, live)}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 36 }}>
        {teamSide(fixture.home_team, fixture.home_logo, homeOutcome)}
        <div style={{ display: "flex", alignItems: "center", gap: 22, fontSize: 128, fontWeight: 800 }}>
          <span style={{ opacity: homeOutcome === "lose" ? 0.5 : 1 }}>{hs}</span>
          <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 80 }}>–</span>
          <span style={{ opacity: awayOutcome === "lose" ? 0.5 : 1 }}>{as}</span>
        </div>
        {teamSide(fixture.away_team, fixture.away_logo, awayOutcome)}
      </div>

      {scorers.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, marginTop: 30 }}>
          {scorers.slice(0, 4).map((line, i) => (
            <div key={i} style={{ display: "flex", fontSize: 24, fontWeight: 600, color: "rgba(255,255,255,0.92)" }}>
              {line}
            </div>
          ))}
        </div>
      ) : null}

      <div style={{ display: "flex", fontSize: 24, color: MUTED, marginTop: 26 }}>
        {kickoffText(fixture.kickoff_utc)}
      </div>
    </div>
  );
}

export function renderShareBanner(fixture: FixtureDetail) {
  const context = fixture.group_name ?? fixture.stage ?? "";
  const homeFlag = flagDataUri(fixture.home_team);
  const awayFlag = flagDataUri(fixture.away_team);
  const content =
    shareBannerVariant(fixture) === "preview"
      ? previewContent(fixture, context)
      : resultContent(fixture, context);
  return shareFrame(homeFlag, awayFlag, content);
}

export function renderFallbackBanner() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: SIZE.width,
        height: SIZE.height,
        fontFamily: "Inter",
        color: "#fff",
        backgroundImage: "linear-gradient(135deg, #0a1430 0%, #122a52 100%)",
      }}
    >
      {brandLockup("lg")}
      <div style={{ display: "flex", fontSize: 30, color: MUTED, marginTop: 24 }}>
        {SITE.domain}
      </div>
    </div>
  );
}

export const shareImageSize = SIZE;
