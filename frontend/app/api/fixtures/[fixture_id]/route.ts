import { getFixture } from "@/lib/api";

// Same-origin proxy so the live match island can poll one fixture without the
// backend URL (API_BASE) reaching the browser, and without CORS. Server-side,
// never cached.
export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ fixture_id: string }> },
) {
  const { fixture_id } = await params;
  const id = Number(fixture_id);
  if (!Number.isFinite(id)) return new Response("Bad request", { status: 400 });
  const fixture = await getFixture(id);
  if (!fixture) return new Response("Not found", { status: 404 });
  return Response.json(fixture, { headers: { "Cache-Control": "no-store" } });
}
