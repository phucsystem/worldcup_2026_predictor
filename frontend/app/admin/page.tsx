import { listFeedback } from "@/lib/api";
import AdminShell from "@/components/admin-shell";
import AdminFeedback from "@/components/admin-feedback";

// Gated by proxy.ts. Feedback is fetched server-side (API_BASE never reaches the
// browser); the client island handles filtering and status changes.
export const dynamic = "force-dynamic";

export default async function AdminFeedbackPage() {
  const feedback = await listFeedback();
  return (
    <AdminShell active="feedback">
      <AdminFeedback initial={feedback} />
    </AdminShell>
  );
}
