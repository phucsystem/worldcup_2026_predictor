"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// The homepage "Up next" section is a static server snapshot: the countdown
// ticks client-side, but nothing re-fetches the route. So when a match kicks
// off and the live poller flips it to in-play, an already-open page keeps
// showing it as upcoming (it just rolls the countdown to "LIVE") instead of
// swapping to the live board/card.
//
// This island closes that gap. While mounted (i.e. while the page is in
// up-next mode), it polls the live endpoint; the moment any match is in play it
// re-fetches the route, after which the server renders the live view and this
// watcher unmounts. It deliberately keys off the live endpoint rather than the
// next kickoff time, because at kickoff the soonest fixture drops out of
// /upcoming before the poller has marked it live — leaving a brief window the
// next-kickoff timestamp can't see.
const POLL_MS = 30_000;

export default function NextKickoffRefresher() {
  const router = useRouter();

  useEffect(() => {
    let active = true;

    async function check() {
      try {
        const res = await fetch("/api/live", { cache: "no-store" });
        if (!res.ok) return;
        const live = await res.json();
        if (active && Array.isArray(live) && live.length > 0) {
          router.refresh();
        }
      } catch {
        // transient failure — try again on the next tick
      }
    }

    check();
    const id = window.setInterval(check, POLL_MS);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [router]);

  return null;
}
