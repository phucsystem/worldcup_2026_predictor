import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import "./globals.css";
import NavLinks from "@/components/nav-links";
import BrandLogo from "@/components/brand-logo";
import SiteBackground from "@/components/site-background";
import CoffeeButton from "@/components/coffee-button";
import FeedbackWidget from "@/components/feedback-widget";
import { SITE } from "@/lib/site";

const DESCRIPTION =
  "World Cup 2026 predictions, live standings, results and AI-written daily intelligence briefs for all 48 teams across USA, Canada and Mexico.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: `World Cup 2026 Predictions, Standings & Daily Briefs · ${SITE.brandName}`,
    template: `%s · ${SITE.brandName}`,
  },
  description: DESCRIPTION,
  applicationName: SITE.brandName,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: SITE.brandName,
    url: "/",
    title: `World Cup 2026 Predictions, Standings & Daily Briefs · ${SITE.brandName}`,
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: `World Cup 2026 Predictions, Standings & Daily Briefs · ${SITE.brandName}`,
    description: DESCRIPTION,
  },
};

const STRUCTURED_DATA = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE.url}/#organization`,
      name: SITE.brandName,
      url: SITE.url,
    },
    {
      "@type": "WebSite",
      "@id": `${SITE.url}/#website`,
      name: SITE.brandName,
      url: SITE.url,
      description: DESCRIPTION,
      publisher: { "@id": `${SITE.url}/#organization` },
      inLanguage: "en",
    },
  ],
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

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(STRUCTURED_DATA) }}
        />

        <SiteBackground />
        <div className="relative z-10 flex min-h-full flex-col">
          <header className="app-header">
            <nav className="nav-inner">
              <Link href="/" aria-label={`${SITE.brandName} — home`} className="brand">
                <BrandLogo height={40} />
              </Link>
              <div className="nav-actions">
                <NavLinks />
                <CoffeeButton />
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
        <FeedbackWidget />
      </body>
    </html>
  );
}
