import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "WC26 Intelligence",
  description: "Daily World Cup 2026 intelligence briefs and standings",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col" style={{ backgroundColor: "#060E22", color: "#FFFFFF" }}>
        <header style={{ backgroundColor: "#0A1B3D", borderBottom: "1px solid #1E3157" }}>
          <nav
            className="flex items-center gap-6 px-6 py-4 overflow-x-auto"
            style={{ maxWidth: "1120px", margin: "0 auto" }}
          >
            <span
              className="font-bold text-lg whitespace-nowrap"
              style={{ color: "#FFFFFF", letterSpacing: "-0.01em" }}
            >
              WC26 Intelligence
            </span>
            <div className="flex gap-5 text-sm font-medium whitespace-nowrap" style={{ color: "#A9B6D4" }}>
              <Link href="/" className="hover:text-white transition-colors" style={{ color: "inherit" }}>
                Today
              </Link>
              <Link href="/standings" className="hover:text-white transition-colors" style={{ color: "inherit" }}>
                Standings
              </Link>
              <Link href="/archive" className="hover:text-white transition-colors" style={{ color: "inherit" }}>
                Archive
              </Link>
            </div>
          </nav>
        </header>

        <main className="flex-1">{children}</main>

        <footer
          className="text-center text-xs py-4 px-6"
          style={{ color: "#6B7A9E", borderTop: "1px solid #1E3157" }}
        >
          Auto-published daily, 7:00 AM Australia/Melbourne
        </footer>
      </body>
    </html>
  );
}
