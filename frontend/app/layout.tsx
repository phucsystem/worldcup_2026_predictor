import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import "./globals.css";
import NavLinks from "@/components/nav-links";
import BrandLogo from "@/components/brand-logo";
import SiteBackground from "@/components/site-background";

export const metadata: Metadata = {
  title: "WC26 Intelligence",
  description: "Daily World Cup 2026 intelligence briefs and standings",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body
        className="min-h-full flex flex-col relative isolate"
        style={{ backgroundColor: "#060E22", color: "#FFFFFF" }}
      >
        {/* Google tag (gtag.js) */}
        <Script
          id="ga-gtag-src"
          src="https://www.googletagmanager.com/gtag/js?id=G-TEJF56N0MN"
          strategy="afterInteractive"
        />
        <Script id="ga-gtag-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-TEJF56N0MN');
          `}
        </Script>

        <SiteBackground />
        <div className="relative z-10 flex min-h-full flex-col">
          <header className="app-header">
            <nav className="nav-inner">
              <Link href="/" aria-label="WC26 Intelligence — home" className="brand">
                <BrandLogo height={40} />
              </Link>
              <div className="nav-actions">
                <NavLinks />
                <span className="coffee-button" aria-label="Support WC26 Intelligence on Buy Me a Coffee">
                  <Script
                    id="buy-me-a-coffee-button"
                    src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js"
                    strategy="afterInteractive"
                    data-name="bmc-button"
                    data-slug="phucsystem"
                    data-color="#FFDD00"
                    data-emoji="☕"
                    data-font="Cookie"
                    data-text="Buy me a coffee"
                    data-outline-color="#000000"
                    data-font-color="#000000"
                    data-coffee-color="#ffffff"
                  />
                </span>
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
        </div>
      </body>
    </html>
  );
}
