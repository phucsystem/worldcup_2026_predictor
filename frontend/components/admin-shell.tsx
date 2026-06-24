import Link from "next/link";
import LogoutButton from "@/components/logout-button";

// Authenticated admin chrome: toolbar + route-based tabs. Feedback (/admin) and
// Logs (/admin/logs) are separate routes so each is deep-linkable.
export default function AdminShell({
  active,
  children,
}: {
  active: "feedback" | "logs";
  children: React.ReactNode;
}) {
  return (
    <div className="admin-page">
      <div className="admin-bar">
        <span className="admin-badge">● Admin</span>
        <LogoutButton />
      </div>
      <h1 className="display-headline" style={{ fontSize: "2rem" }}>
        Admin
      </h1>
      <nav className="admin-tabs" aria-label="Admin sections">
        <Link className={`toggle-btn${active === "feedback" ? " active" : ""}`} href="/admin">
          Feedback
        </Link>
        <Link className={`toggle-btn${active === "logs" ? " active" : ""}`} href="/admin/logs">
          Logs
        </Link>
      </nav>
      {children}
    </div>
  );
}
