import { submitFeedback } from "@/lib/api";

// Same-origin proxy: the public widget POSTs here; we forward server-side to the
// backend so API_BASE never reaches the browser and CORS stays GET-only.
export const dynamic = "force-dynamic";

const MESSAGE_MAX = 2000;

export async function POST(request: Request) {
  let message = "";
  let topic: string | null = null;
  let page: string | null = null;
  try {
    const body = await request.json();
    message = typeof body?.message === "string" ? body.message.trim() : "";
    topic = typeof body?.topic === "string" ? body.topic : null;
    page = typeof body?.page === "string" ? body.page.slice(0, 200) : null;
  } catch {
    message = "";
  }

  if (!message || message.length > MESSAGE_MAX) {
    return Response.json({ error: "invalid message" }, { status: 422 });
  }

  const ok = await submitFeedback({ message, topic, page });
  return ok
    ? Response.json({ ok: true }, { status: 201 })
    : Response.json({ error: "feedback unavailable" }, { status: 502 });
}
