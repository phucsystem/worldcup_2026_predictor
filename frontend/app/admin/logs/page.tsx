import LogsView from "@/components/logs-view";
import AdminShell from "@/components/admin-shell";

// System logs, relocated from the former public /logs route into the gated
// admin area (proxy.ts enforces the session).
export const dynamic = "force-dynamic";

export default function AdminLogsPage() {
  return (
    <AdminShell active="logs">
      <p className="summary-deck" style={{ fontSize: 15, marginBottom: "var(--space-4)" }}>
        Info and error events from the daily pipeline, scheduler, and data collector. Newest first.
      </p>
      <LogsView />
    </AdminShell>
  );
}
