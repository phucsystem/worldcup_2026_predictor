// Site-wide brand + domain config. Swap these when a dedicated domain lands;
// nothing else hardcodes the domain or brand name.
export const SITE = {
  /** Public domain shown on share images. No protocol. */
  domain: "wc2026.phucsystemlabs.com",
  /** Brand name for titles, aria labels, share text. */
  brandName: "WC26 Intelligence",
  /** Share-image wordmark lockup: primary + accent halves and the subline. */
  wordmark: { primary: "WC", accent: "26", sub: "INTELLIGENCE" },
} as const;
