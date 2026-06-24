import { ImageResponse } from "next/og";
import { getFixture } from "@/lib/api";
import {
  renderShareBanner,
  loadShareFonts,
  isLiveFixture,
  shareImageSize,
  parseFixtureId,
} from "@/lib/share-banner";

export const runtime = "nodejs";
// Generated per request: finished images are CDN-cached by the response header,
// live images are no-store. Either way the handler must run on each request.
export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ fixture_id: string }> },
) {
  const { fixture_id } = await params;
  const id = parseFixtureId(fixture_id);
  if (id === null) {
    return new Response("Invalid fixture id", { status: 400 });
  }
  const fixture = await getFixture(id);
  if (!fixture) {
    return new Response("Fixture not found", { status: 404 });
  }
  try {
    const fonts = await loadShareFonts();
    const cacheControl = isLiveFixture(fixture)
      ? "no-store"
      : "public, max-age=86400, immutable";
    return new ImageResponse(renderShareBanner(fixture), {
      ...shareImageSize,
      fonts,
      headers: { "Cache-Control": cacheControl },
    });
  } catch (e) {
    console.error("share-image render failed", e);
    return new Response("Failed to generate image", { status: 500 });
  }
}
