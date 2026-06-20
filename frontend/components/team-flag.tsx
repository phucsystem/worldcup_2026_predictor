"use client";

import { useState } from "react";

interface Props {
  team: string | null;
  logo?: string | null;
  size?: number;
}

function initials(team: string | null): string {
  if (!team) return "?";
  const parts = team.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * National crest as a small flag. Falls back to a colored initials badge when
 * the logo is missing or fails to load (external images can 404/be offline).
 */
export default function TeamFlag({ team, logo, size = 20 }: Props) {
  const [errored, setErrored] = useState(false);
  const dim = `${size}px`;

  if (!logo || errored) {
    return (
      <span
        aria-hidden="true"
        className="inline-flex items-center justify-center shrink-0 font-bold"
        style={{
          width: dim,
          height: dim,
          fontSize: `${Math.round(size * 0.42)}px`,
          backgroundColor: "#13294F",
          color: "#A9B6D4",
          borderRadius: "4px",
        }}
      >
        {initials(team)}
      </span>
    );
  }

  return (
    <img
      src={logo}
      alt=""
      aria-hidden="true"
      width={size}
      height={size}
      loading="lazy"
      onError={() => setErrored(true)}
      className="inline-block shrink-0 object-contain"
      style={{ width: dim, height: dim, borderRadius: "4px" }}
    />
  );
}
