import { ImageResponse } from "next/og";
import { getFixture } from "@/lib/api";
import {
  renderShareBanner,
  renderFallbackBanner,
  loadShareFonts,
  shareImageSize,
  parseFixtureId,
} from "@/lib/share-banner";

export const alt = "Match result";
export const size = shareImageSize;
export const contentType = "image/png";
export const runtime = "nodejs";
// Regenerate per request so a live score is never frozen into the link preview.
export const dynamic = "force-dynamic";

export default async function Image({ params }: { params: Promise<{ fixture_id: string }> }) {
  const { fixture_id } = await params;
  const fonts = await loadShareFonts();
  const id = parseFixtureId(fixture_id);
  const fixture = id === null ? null : await getFixture(id);
  // Crawlers should still get a valid card for an unknown id, not a 404.
  const element = fixture ? renderShareBanner(fixture) : renderFallbackBanner();
  return new ImageResponse(element, { ...size, fonts });
}
