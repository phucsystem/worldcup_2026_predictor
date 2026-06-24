"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Mascot, { type MascotKind } from "@/components/mascot";

type Topic = "bug" | "feature" | "other";
type Phase = "greeting" | "compose" | "thanks";

const PROMPTS: { topic: Topic; label: string }[] = [
  { topic: "bug", label: "🐞 Report a bug" },
  { topic: "feature", label: "💡 Suggest a feature" },
  { topic: "other", label: "💬 Something else" },
];

const FOLLOW_UP: Record<Topic, string> = {
  bug: "Oh no — what broke? Tell me what you saw and where.",
  feature: "Love it! What would make the platform better for you?",
  other: "Go ahead — I'm all ears (well, antlers).",
};

const TRIO: MascotKind[] = ["moose", "jaguar", "eagle"];

export default function FeedbackWidget() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [phase, setPhase] = useState<Phase>("greeting");
  const [topic, setTopic] = useState<Topic | null>(null);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  // Public surface only — never on the admin pages.
  if (pathname?.startsWith("/admin")) return null;

  const followMascot = TRIO[topic ? PROMPTS.findIndex((p) => p.topic === topic) : 0];

  function pick(t: Topic) {
    setTopic(t);
    setPhase("compose");
  }

  async function submit() {
    const message = text.trim();
    if (!message || sending) return;
    setSending(true);
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, topic, page: pathname || "/" }),
      });
    } catch {
      // Best-effort; still thank the user (matches the prototype's optimism).
    }
    setPhase("thanks");
    setSending(false);
  }

  function reset() {
    setOpen(false);
    // Reset after the close animation so it doesn't flash mid-collapse.
    setTimeout(() => {
      setPhase("greeting");
      setTopic(null);
      setText("");
    }, 250);
  }

  return (
    <>
      <button
        className="fb-fab"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => (open ? reset() : setOpen(true))}
      >
        <Mascot kind="moose" size={40} />
        <span>Feedback</span>
        {!open && <span className="fab-ping" aria-hidden="true" />}
      </button>

      {open && (
        <section className="fb-panel" role="dialog" aria-label="Supporter feedback">
          <header className="fb-head">
            <span className="fb-head-trio">
              {TRIO.map((k) => (
                <Mascot key={k} kind={k} size={38} />
              ))}
            </span>
            <div className="fb-head-titles">
              <div className="fb-head-title">Host Supporters</div>
              <div className="fb-head-sub">
                <span className="dot" /> here to help · replies instantly
              </div>
            </div>
            <button className="fb-close" aria-label="Close feedback" onClick={reset}>
              &times;
            </button>
          </header>

          {phase === "thanks" ? (
            <div className="fb-body">
              <div className="fb-thanks">
                <Mascot kind={followMascot} size={64} className="lg" />
                <h3>Thank you! 🎉</h3>
                <p>Your feedback is in. The supporters are on it.</p>
              </div>
            </div>
          ) : (
            <>
              <div className="fb-body">
                <div className="fb-msg bot">
                  <Mascot kind="moose" size={30} idle />
                  <div className="fb-bubble">
                    {phase === "greeting"
                      ? "Hey, supporter! 🍁 What's on your mind about the platform?"
                      : FOLLOW_UP[topic!]}
                  </div>
                </div>
                {phase === "greeting" && (
                  <div className="fb-prompts">
                    {PROMPTS.map((p) => (
                      <button key={p.topic} className="fb-prompt" onClick={() => pick(p.topic)}>
                        {p.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {phase === "compose" && (
                <div className="fb-composer">
                  <textarea
                    className="fb-input"
                    rows={1}
                    placeholder="Type your feedback…"
                    autoFocus
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        submit();
                      }
                    }}
                  />
                  <button
                    className="fb-send"
                    aria-label="Send feedback"
                    disabled={!text.trim() || sending}
                    onClick={submit}
                  >
                    <svg viewBox="0 0 24 24" width={20} height={20} fill="currentColor" aria-hidden="true">
                      <path d="M3 11l18-8-8 18-2-7-8-3z" />
                    </svg>
                  </button>
                </div>
              )}
              <div className="fb-context">🔒 We attach the page you&apos;re on. No account needed.</div>
            </>
          )}
        </section>
      )}
    </>
  );
}
