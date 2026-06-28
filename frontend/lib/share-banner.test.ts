import { describe, it, expect } from "vitest";
import { isLiveFixture, shareBannerVariant } from "./share-banner";
import type { FixtureDetail } from "./api";

function fixture(status: string | null, kickoffOffsetMs: number | null): FixtureDetail {
  const kickoff_utc =
    kickoffOffsetMs == null ? null : new Date(Date.now() + kickoffOffsetMs).toISOString();
  return { status, kickoff_utc } as FixtureDetail;
}

describe("isLiveFixture", () => {
  it("is true for an in-play status", () => {
    expect(isLiveFixture(fixture("2H", -3_600_000))).toBe(true);
    expect(isLiveFixture(fixture("HT", -3_600_000))).toBe(true);
  });

  it("is false for a finished match", () => {
    expect(isLiveFixture(fixture("FT", -7_200_000))).toBe(false);
  });

  it("is true for a kicked-off match whose status hasn't flipped to live yet", () => {
    // The poller-lag case that caused the share image to show 'VS' for a live game.
    expect(isLiveFixture(fixture("NS", -5 * 60_000))).toBe(true);
  });

  it("is false for a genuinely upcoming match (kickoff in the future)", () => {
    expect(isLiveFixture(fixture("NS", 60 * 60_000))).toBe(false);
  });

  it("is false when kickoff is unknown and status is not live", () => {
    expect(isLiveFixture(fixture("NS", null))).toBe(false);
  });
});

describe("shareBannerVariant", () => {
  it("draws the score layout for live and finished matches", () => {
    expect(shareBannerVariant(fixture("2H", -3_600_000))).toBe("result");
    expect(shareBannerVariant(fixture("FT", -7_200_000))).toBe("result");
  });

  it("draws the score layout for a kicked-off match stuck at NS (the bug fix)", () => {
    expect(shareBannerVariant(fixture("NS", -5 * 60_000))).toBe("result");
  });

  it("draws the VS preview only for a genuinely upcoming match", () => {
    expect(shareBannerVariant(fixture("NS", 60 * 60_000))).toBe("preview");
    expect(shareBannerVariant(fixture("NS", null))).toBe("preview");
  });
});
