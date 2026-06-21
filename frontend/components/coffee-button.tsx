import { Cookie } from "next/font/google";

// The official BMC widget renders via document.writeln(), which is a no-op once
// the page has parsed — so it never appears in a React/Next SPA. This is a
// static, SSR-safe replica of the button (same colours/emoji/Cookie font) that
// links straight to the profile.
const cookie = Cookie({ weight: "400", subsets: ["latin"], display: "swap" });

export default function CoffeeButton() {
  return (
    <a
      href="https://www.buymeacoffee.com/phucsystem"
      target="_blank"
      rel="noopener noreferrer"
      className={`coffee-button ${cookie.className}`}
      aria-label="Buy me a coffee — support WC26 Intelligence"
    >
      <span className="coffee-emoji" aria-hidden="true">
        ☕
      </span>
      <span className="coffee-text">Buy me a coffee</span>
    </a>
  );
}
