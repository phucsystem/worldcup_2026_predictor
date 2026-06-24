"use client";

import { useState } from "react";

interface Props {
  fixtureId: number;
  label?: string;
  shareTitle?: string;
}

type Status = "idle" | "working" | "copied" | "shared" | "downloaded" | "error";

const MESSAGES: Record<Status, string> = {
  idle: "",
  working: "Generating…",
  copied: "Image copied — paste it to a friend",
  shared: "Shared",
  downloaded: "Image downloaded",
  error: "Couldn't share — try again",
};

const DONE: Status[] = ["copied", "shared", "downloaded"];

function Icon({ status }: { status: Status }) {
  const common = {
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  if (status === "working") {
    return (
      <svg {...common} className="share-spin">
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </svg>
    );
  }
  if (DONE.includes(status)) {
    return (
      <svg {...common}>
        <polyline points="20 6 9 17 4 12" />
      </svg>
    );
  }
  if (status === "error") {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    );
  }
  // idle — share / upload glyph
  return (
    <svg {...common}>
      <path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  );
}

function downloadBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Desktop-first share: copy the server-rendered PNG to the clipboard (the
// ClipboardItem is built synchronously from the fetch promise so Safari keeps
// the user-activation), then fall back to the native share sheet, then download.
export default function ShareResultButton({ fixtureId, label = "Share result", shareTitle = "World Cup 2026" }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const url = `/match/${fixtureId}/share-image`;
  const fileName = `wc2026-match-${fixtureId}.png`;

  async function handleClick() {
    setStatus("working");

    // One fetch shared by both paths. Built before clipboard.write so the
    // ClipboardItem receives a promise synchronously (keeps Safari's
    // user-activation), and reused by the share/download fallback.
    const blobPromise = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`share-image ${r.status}`);
      return r.blob();
    });

    if (typeof ClipboardItem !== "undefined" && navigator.clipboard?.write) {
      try {
        await navigator.clipboard.write([new ClipboardItem({ "image/png": blobPromise })]);
        setStatus("copied");
        resetSoon();
        return;
      } catch {
        // fall through to share / download, reusing the same in-flight blob
      }
    }

    try {
      const blob = await blobPromise;
      const file = new File([blob], fileName, { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: shareTitle });
        setStatus("shared");
      } else {
        downloadBlob(blob, fileName);
        setStatus("downloaded");
      }
      resetSoon();
    } catch {
      setStatus("error");
      resetSoon();
    }
  }

  function resetSoon() {
    setTimeout(() => setStatus("idle"), 4000);
  }

  return (
    <span className="share-result">
      <button
        type="button"
        className="share-result-btn"
        data-status={status}
        onClick={handleClick}
        disabled={status === "working"}
        aria-label={label}
      >
        <span className="share-ico" aria-hidden="true">
          <Icon status={status} />
        </span>
        {label}
      </button>
      <span className="share-result-status" role="status" aria-live="polite">
        {MESSAGES[status]}
      </span>
    </span>
  );
}
