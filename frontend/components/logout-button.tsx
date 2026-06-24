"use client";

import { useRouter } from "next/navigation";

export default function LogoutButton() {
  const router = useRouter();
  async function logout() {
    await fetch("/api/admin/session", { method: "DELETE" });
    router.replace("/admin/login");
    router.refresh();
  }
  return (
    <button className="btn ghost" onClick={logout} type="button">
      Log out
    </button>
  );
}
