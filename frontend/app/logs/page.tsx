import LogsView from "@/components/logs-view";

// Unlinked ops console — reachable at /logs but intentionally absent from the
// top nav (see nav-links.tsx). Rendered dynamically; the island fetches the
// same-origin /api/logs proxy so API_BASE never reaches the browser.
export const dynamic = "force-dynamic";

export default function LogsPage() {
  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <div style={{ marginBottom: "var(--space-6)" }}>
        <h1 className="page-title">System logs</h1>
        <p className="summary-deck" style={{ marginTop: "var(--space-2)" }}>
          Info and error events from the daily pipeline, scheduler, and data collector. Newest first.
        </p>
      </div>
      <LogsView />
    </div>
  );
}
