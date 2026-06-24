"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Mascot from "@/components/mascot";

export default function AdminLoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    const res = await fetch("/api/admin/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    if (res.ok) {
      router.replace("/admin");
      router.refresh();
    } else {
      setError("Incorrect password.");
      setBusy(false);
    }
  }

  return (
    <div className="admin-login-wrap">
      <form className="admin-login" onSubmit={submit}>
        <Mascot kind="eagle" size={64} idle className="lg" />
        <h1>Admin access</h1>
        <p>Restricted area · single administrator</p>

        <div className="admin-field">
          <label htmlFor="admin-pw">Password</label>
          <input
            id="admin-pw"
            className="admin-input"
            type="password"
            autoComplete="current-password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-invalid={error ? true : undefined}
          />
          {error && (
            <p role="alert" style={{ color: "var(--status-loss)", fontSize: 13, marginTop: 8 }}>
              {error}
            </p>
          )}
        </div>

        <button className="btn" type="submit" disabled={busy || !password}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <div className="admin-note">🔒 Your session is remembered on this device after login.</div>
      </form>
    </div>
  );
}
