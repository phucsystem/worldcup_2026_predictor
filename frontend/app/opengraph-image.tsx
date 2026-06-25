import { ImageResponse } from "next/og";
import { renderFallbackBanner, loadShareFonts, shareImageSize } from "@/lib/share-banner";
import { SITE } from "@/lib/site";

export const alt = `${SITE.brandName} — World Cup 2026 predictions, standings and daily briefs`;
export const size = shareImageSize;
export const contentType = "image/png";
export const runtime = "nodejs";

// Default share card for every page without its own opengraph-image (home, standings,
// results, fixtures, archive, briefs). Match pages override this with a live scoreline.
export default async function Image() {
  const fonts = await loadShareFonts();
  return new ImageResponse(renderFallbackBanner(), { ...size, fonts });
}
