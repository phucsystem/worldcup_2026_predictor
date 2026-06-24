import { requireAdmin } from "@/lib/admin-auth";
import { updateFeedbackStatus, type FeedbackStatus } from "@/lib/api";

// Authenticated status update. proxy.ts already gates /admin/*, but admin APIs
// re-check the session here (defence-in-depth) so they 401 if hit directly.
export const dynamic = "force-dynamic";

const STATUSES: FeedbackStatus[] = ["new", "done", "wont"];

export async function PATCH(request: Request, ctx: { params: Promise<{ id: string }> }) {
  if (!requireAdmin(request)) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }

  const { id } = await ctx.params;
  const feedbackId = Number(id);
  if (!Number.isInteger(feedbackId) || feedbackId <= 0) {
    return Response.json({ error: "invalid id" }, { status: 400 });
  }

  let status: string | undefined;
  try {
    status = (await request.json())?.status;
  } catch {
    status = undefined;
  }
  if (!status || !STATUSES.includes(status as FeedbackStatus)) {
    return Response.json({ error: "invalid status" }, { status: 422 });
  }

  const ok = await updateFeedbackStatus(feedbackId, status as FeedbackStatus);
  return ok
    ? new Response(null, { status: 204 })
    : Response.json({ error: "not found" }, { status: 404 });
}
