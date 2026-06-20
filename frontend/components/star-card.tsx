"use client";

import { useState } from "react";
import type { StarRow } from "@/lib/api";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Top-scorer card: circular player photo (initials fallback on load error),
 * goal count, name + team. */
export default function StarCard({ player }: { player: StarRow }) {
  const [errored, setErrored] = useState(false);
  const showPhoto = player.photo_url && !errored;

  return (
    <article
      className="flex items-center gap-3 p-3 border shrink-0"
      style={{ backgroundColor: "#0A1B3D", borderColor: "#1E3157", borderRadius: "12px", minWidth: "220px" }}
    >
      {showPhoto ? (
        <img
          src={player.photo_url as string}
          alt=""
          aria-hidden="true"
          width={44}
          height={44}
          loading="lazy"
          onError={() => setErrored(true)}
          className="object-cover shrink-0"
          style={{ width: 44, height: 44, borderRadius: "50%" }}
        />
      ) : (
        <span
          aria-hidden="true"
          className="inline-flex items-center justify-center shrink-0 font-bold text-sm"
          style={{ width: 44, height: 44, borderRadius: "50%", backgroundColor: "#13294F", color: "#A9B6D4" }}
        >
          {initials(player.name)}
        </span>
      )}
      <div className="min-w-0">
        <p className="text-sm font-semibold truncate" style={{ color: "#FFFFFF" }}>
          {player.name}
        </p>
        <p className="text-xs truncate" style={{ color: "#6B7A9E" }}>
          {player.team ?? "—"}
        </p>
      </div>
      <span
        className="ml-auto text-sm font-bold tabular-nums"
        style={{ color: "#2BD37E" }}
        aria-label={`${player.goals} goals`}
      >
        {player.goals}
        <span aria-hidden="true" className="text-xs font-normal" style={{ color: "#6B7A9E" }}>
          {" "}G
        </span>
      </span>
    </article>
  );
}
