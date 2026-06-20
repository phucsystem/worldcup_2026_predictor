import { getLogs } from "@/lib/api";

// Same-origin proxy so the client console can page/filter logs without the
// backend URL (API_BASE) ever reaching the browser, and without CORS. Runs
// server-side; never cached.
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const sp = new URL(request.url).searchParams;
  const limit = sp.get("limit");
  const offset = sp.get("offset");
  try {
    const page = await getLogs({
      level: sp.get("level") ?? undefined,
      q: sp.get("q") ?? undefined,
      source: sp.get("source") ?? undefined,
      limit: limit != null ? Number(limit) : undefined,
      offset: offset != null ? Number(offset) : undefined,
    });
    return Response.json(page, { headers: { "Cache-Control": "no-store" } });
  } catch {
    // Surface upstream failure as a real error so the client renders its error
    // state instead of an empty page.
    return Response.json(
      { error: "logs unavailable" },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
