// Inline SVG flags (viewBox 0 0 30 20), ported verbatim from the prototype's
// single source of truth (prototypes/interactions.js). Simplified geometric
// flags so they stay self-contained and render identically across platforms.
export const FLAGS: Record<string, string> = {
  br: '<rect width="30" height="20" fill="#009C3B"/><polygon points="15,2.5 27.5,10 15,17.5 2.5,10" fill="#FFDF00"/><circle cx="15" cy="10" r="4" fill="#002776"/>',
  ar: '<rect width="30" height="20" fill="#74ACDF"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><circle cx="15" cy="10" r="2.3" fill="#F6B40E"/>',
  mx: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#006847"/><rect x="20" width="10" height="20" fill="#CE1126"/><circle cx="15" cy="10" r="1.8" fill="#9b7a4a"/>',
  rs: '<rect width="30" height="20" fill="#fff"/><rect width="30" height="6.67" fill="#C6363C"/><rect y="6.67" width="30" height="6.67" fill="#0C4076"/>',
  ch: '<rect width="30" height="20" fill="#D52B1E"/><rect x="13" y="4" width="4" height="12" fill="#fff"/><rect x="9" y="8" width="12" height="4" fill="#fff"/>',
  cm: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#007A5E"/><rect x="20" width="10" height="20" fill="#CE1126"/><circle cx="15" cy="10" r="2" fill="#FCD116"/>',
  pt: '<rect width="30" height="20" fill="#FF0000"/><rect width="12" height="20" fill="#006600"/><circle cx="12" cy="10" r="3" fill="#FFD43B" stroke="#fff" stroke-width="0.4"/>',
  gh: '<rect width="30" height="20" fill="#CE1126"/><rect y="6.67" width="30" height="6.67" fill="#FCD116"/><rect y="13.33" width="30" height="6.67" fill="#006B3F"/><circle cx="15" cy="10" r="1.9" fill="#000"/>',
  uy: '<rect width="30" height="20" fill="#fff"/><rect y="3" width="30" height="1.9" fill="#0038A8"/><rect y="7.4" width="30" height="1.9" fill="#0038A8"/><rect y="11.8" width="30" height="1.9" fill="#0038A8"/><rect y="16.2" width="30" height="1.9" fill="#0038A8"/><rect width="12" height="9.3" fill="#fff"/><circle cx="6" cy="4.6" r="2.2" fill="#FCD116"/>',
  kr: '<rect width="30" height="20" fill="#fff"/><path d="M12 10 a3 3 0 0 1 6 0 z" fill="#CD2E3A"/><path d="M12 10 a3 3 0 0 0 6 0 z" fill="#0047A0"/>',
  pl: '<rect width="30" height="20" fill="#fff"/><rect y="10" width="30" height="10" fill="#DC143C"/>',
  sa: '<rect width="30" height="20" fill="#006C35"/><rect x="4" y="8" width="22" height="3.4" rx="0.4" fill="#fff"/><rect x="6" y="12.4" width="18" height="1" fill="#fff"/>',
  fr: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#0055A4"/><rect x="20" width="10" height="20" fill="#EF4135"/>',
  au: '<rect width="30" height="20" fill="#00008B"/><path d="M0 0 L12 10 M12 0 L0 10" stroke="#fff" stroke-width="2"/><path d="M0 0 L12 10 M12 0 L0 10" stroke="#C8102E" stroke-width="0.8"/><path d="M6 0 V10 M0 5 H12" stroke="#fff" stroke-width="2.6"/><path d="M6 0 V10 M0 5 H12" stroke="#C8102E" stroke-width="1.3"/><circle cx="6" cy="15" r="1.7" fill="#fff"/><circle cx="22" cy="5" r="1" fill="#fff"/><circle cx="26" cy="9" r="1" fill="#fff"/><circle cx="22.5" cy="13.5" r="1" fill="#fff"/><circle cx="25" cy="16" r="0.8" fill="#fff"/><circle cx="24" cy="10" r="0.6" fill="#fff"/>',
  no: '<rect width="30" height="20" fill="#BA0C2F"/><path d="M11 0 V20 M0 10 H30" stroke="#fff" stroke-width="5"/><path d="M11 0 V20 M0 10 H30" stroke="#00205B" stroke-width="2.6"/>',
  hr: '<rect width="30" height="20" fill="#fff"/><rect width="30" height="6.67" fill="#FF0000"/><rect y="13.33" width="30" height="6.67" fill="#171796"/><rect x="12.5" y="6" width="5" height="7" fill="#fff" stroke="#FF0000" stroke-width="0.5"/><rect x="12.5" y="6" width="2.5" height="3.5" fill="#FF0000"/><rect x="15" y="9.5" width="2.5" height="3.5" fill="#FF0000"/>',
  nz: '<rect width="30" height="20" fill="#00247D"/><path d="M0 0 L12 10 M12 0 L0 10" stroke="#fff" stroke-width="2"/><path d="M0 0 L12 10 M12 0 L0 10" stroke="#C8102E" stroke-width="0.8"/><path d="M6 0 V10 M0 5 H12" stroke="#fff" stroke-width="2.6"/><path d="M6 0 V10 M0 5 H12" stroke="#C8102E" stroke-width="1.3"/><circle cx="23" cy="6" r="1.1" fill="#CC142B" stroke="#fff" stroke-width="0.4"/><circle cx="26.5" cy="10" r="1.1" fill="#CC142B" stroke="#fff" stroke-width="0.4"/><circle cx="22.5" cy="14" r="1.1" fill="#CC142B" stroke="#fff" stroke-width="0.4"/><circle cx="25" cy="16.5" r="0.9" fill="#CC142B" stroke="#fff" stroke-width="0.4"/>',
  ca: '<rect width="30" height="20" fill="#fff"/><rect width="7" height="20" fill="#D80621"/><rect x="23" width="7" height="20" fill="#D80621"/><path d="M15 4 L16.2 8 L19 7 L17.2 9.6 L20 11 L16.7 11.3 L17.2 15 L15 12.6 L12.8 15 L13.3 11.3 L10 11 L12.8 9.6 L11 7 L13.8 8 Z" fill="#D80621"/>',
  us: '<rect width="30" height="20" fill="#B22234"/><path d="M0 2.85 H30 M0 5.7 H30 M0 8.55 H30 M0 11.4 H30 M0 14.25 H30 M0 17.1 H30" stroke="#fff" stroke-width="1.42"/><rect width="13" height="10.8" fill="#3C3B6E"/>',
  co: '<rect width="30" height="20" fill="#CE1126"/><rect width="30" height="10" fill="#FCD116"/><rect y="10" width="30" height="5" fill="#003893"/>',
  ec: '<rect width="30" height="20" fill="#ED1C24"/><rect width="30" height="10" fill="#FFDD00"/><rect y="10" width="30" height="5" fill="#034EA2"/><circle cx="15" cy="10" r="2" fill="#8B6F35"/>',
  pe: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#D91023"/><rect x="20" width="10" height="20" fill="#D91023"/>',
  cl: '<rect width="30" height="20" fill="#fff"/><rect y="10" width="30" height="10" fill="#D52B1E"/><rect width="12" height="10" fill="#0039A6"/><circle cx="6" cy="5" r="1.8" fill="#fff"/>',
  de: '<rect width="30" height="20" fill="#FFCE00"/><rect width="30" height="6.67" fill="#000"/><rect y="6.67" width="30" height="6.67" fill="#DD0000"/>',
  es: '<rect width="30" height="20" fill="#AA151B"/><rect y="5" width="30" height="10" fill="#F1BF00"/><rect x="8" y="8" width="3.2" height="4" fill="#AA151B"/>',
  nl: '<rect width="30" height="20" fill="#21468B"/><rect width="30" height="6.67" fill="#AE1C28"/><rect y="6.67" width="30" height="6.67" fill="#fff"/>',
  be: '<rect width="30" height="20" fill="#FAE042"/><rect width="10" height="20" fill="#000"/><rect x="20" width="10" height="20" fill="#ED2939"/>',
  dk: '<rect width="30" height="20" fill="#C60C30"/><path d="M10 0 V20 M0 10 H30" stroke="#fff" stroke-width="3.3"/>',
  se: '<rect width="30" height="20" fill="#006AA7"/><path d="M10 0 V20 M0 10 H30" stroke="#FECC00" stroke-width="3.3"/>',
  eng: '<rect width="30" height="20" fill="#fff"/><path d="M15 0 V20 M0 10 H30" stroke="#CE1124" stroke-width="3"/>',
  it: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#009246"/><rect x="20" width="10" height="20" fill="#CE2B37"/>',
  ma: '<rect width="30" height="20" fill="#C1272D"/><path d="M15 5.2 L16.2 8.8 H20 L16.9 11 L18.1 14.6 L15 12.4 L11.9 14.6 L13.1 11 L10 8.8 H13.8 Z" fill="none" stroke="#006233" stroke-width="1.2"/>',
  sn: '<rect width="30" height="20" fill="#FDEF42"/><rect width="10" height="20" fill="#00853F"/><rect x="20" width="10" height="20" fill="#E31B23"/><path d="M15 6 L16 9 H19 L16.6 10.8 L17.5 14 L15 12 L12.5 14 L13.4 10.8 L11 9 H14 Z" fill="#00853F"/>',
  ng: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#008751"/><rect x="20" width="10" height="20" fill="#008751"/>',
  eg: '<rect width="30" height="20" fill="#000"/><rect width="30" height="6.67" fill="#CE1126"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><circle cx="15" cy="10" r="1.6" fill="#C09300"/>',
  za: '<rect width="30" height="20" fill="#002395"/><rect y="10" width="30" height="10" fill="#DE3831"/><path d="M0 0 L14 10 L0 20 Z" fill="#000"/><path d="M0 0 L15.5 10 L0 20" fill="none" stroke="#FFB612" stroke-width="4"/><path d="M0 0 L18 10 L0 20" fill="none" stroke="#007A4D" stroke-width="2.4"/><path d="M14 0 H30 M14 20 H30" stroke="#fff" stroke-width="4"/><path d="M15.5 0 H30 M15.5 20 H30" stroke="#007A4D" stroke-width="2.2"/>',
  jp: '<rect width="30" height="20" fill="#fff"/><circle cx="15" cy="10" r="4.5" fill="#BC002D"/>',
  ir: '<rect width="30" height="20" fill="#DA0000"/><rect width="30" height="6.67" fill="#239F40"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><circle cx="15" cy="10" r="1.5" fill="#DA0000"/>',
  qa: '<rect width="30" height="20" fill="#8A1538"/><path d="M0 0 H9 L5.8 1.1 L9 2.2 L5.8 3.3 L9 4.4 L5.8 5.5 L9 6.6 L5.8 7.7 L9 8.8 L5.8 9.9 L9 11 L5.8 12.1 L9 13.2 L5.8 14.3 L9 15.4 L5.8 16.5 L9 17.6 L5.8 18.8 L9 20 H0 Z" fill="#fff"/>',
  cr: '<rect width="30" height="20" fill="#002B7F"/><rect y="3.1" width="30" height="13.8" fill="#fff"/><rect y="6.4" width="30" height="7.2" fill="#CE1126"/>',
  pa: '<rect width="30" height="20" fill="#fff"/><rect x="15" width="15" height="10" fill="#D21034"/><rect y="10" width="15" height="10" fill="#005293"/><path d="M7.5 3 L8.4 5.7 H11.2 L8.9 7.4 L9.8 10 L7.5 8.4 L5.2 10 L6.1 7.4 L3.8 5.7 H6.6 Z" fill="#005293"/><path d="M22.5 13 L23.4 15.7 H26.2 L23.9 17.4 L24.8 20 L22.5 18.4 L20.2 20 L21.1 17.4 L18.8 15.7 H21.6 Z" fill="#D21034"/>',
  jm: '<rect width="30" height="20" fill="#009B3A"/><path d="M0 0 L30 20 M30 0 L0 20" stroke="#FED100" stroke-width="4"/><path d="M0 0 L12 10 L0 20 Z M30 0 L18 10 L30 20 Z" fill="#000"/>',
  tn: '<rect width="30" height="20" fill="#E70013"/><circle cx="15" cy="10" r="5.4" fill="#fff"/><circle cx="16" cy="10" r="3.1" fill="#E70013"/><circle cx="17.2" cy="10" r="2.5" fill="#fff"/><path d="M16.8 7.6 L17.4 9.2 H19.1 L17.7 10.2 L18.3 11.8 L16.8 10.8 L15.4 11.8 L15.9 10.2 L14.5 9.2 H16.2 Z" fill="#E70013"/>',
  dz: '<rect width="30" height="20" fill="#fff"/><rect width="15" height="20" fill="#006233"/><circle cx="16" cy="10" r="4" fill="#D21034"/><circle cx="17.3" cy="10" r="3.4" fill="#fff"/><path d="M19 7.5 L19.8 9.3 H21.7 L20.2 10.4 L20.8 12.2 L19 11.1 L17.4 12.2 L18 10.4 L16.5 9.3 H18.3 Z" fill="#D21034"/>',
  ci: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#F77F00"/><rect x="20" width="10" height="20" fill="#009E60"/>',
  ua: '<rect width="30" height="20" fill="#FFD700"/><rect width="30" height="10" fill="#0057B7"/>',
  at: '<rect width="30" height="20" fill="#ED2939"/><rect y="6.67" width="30" height="6.67" fill="#fff"/>',
  cz: '<rect width="30" height="20" fill="#D7141A"/><rect width="30" height="10" fill="#fff"/><path d="M0 0 L15 10 L0 20 Z" fill="#11457E"/>',
  iq: '<rect width="30" height="20" fill="#000"/><rect width="30" height="6.67" fill="#CE1126"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><path d="M10 10 H20" stroke="#007A3D" stroke-width="1.4" stroke-linecap="round"/>',
  jo: '<rect width="30" height="20" fill="#007A3D"/><rect width="30" height="6.67" fill="#000"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><path d="M0 0 L14 10 L0 20 Z" fill="#CE1126"/><circle cx="5" cy="10" r="1.1" fill="#fff"/>',
  uz: '<rect width="30" height="20" fill="#1EB53A"/><rect width="30" height="9" fill="#0099B5"/><rect y="9" width="30" height="2" fill="#CE1126"/><rect y="11" width="30" height="5" fill="#fff"/><circle cx="5.5" cy="4.5" r="2.2" fill="#fff"/><circle cx="6.2" cy="4.5" r="2.2" fill="#0099B5"/>',
  cv: '<rect width="30" height="20" fill="#003893"/><rect y="11" width="30" height="3" fill="#fff"/><rect y="12" width="30" height="1" fill="#CF2027"/>',
  cd: '<rect width="30" height="20" fill="#007FFF"/><path d="M-2 20 L30 -2" stroke="#F7D618" stroke-width="6"/><path d="M-2 20 L30 -2" stroke="#CE1021" stroke-width="3"/><path d="M6 2 L7.1 5.3 H10.5 L7.7 7.3 L8.8 10.5 L6 8.5 L3.2 10.5 L4.3 7.3 L1.5 5.3 H4.9 Z" fill="#F7D618"/>',
  cw: '<rect width="30" height="20" fill="#002B7F"/><rect y="13" width="30" height="2.2" fill="#F9E814"/><circle cx="7.5" cy="5.5" r="1.4" fill="#fff"/><circle cx="11" cy="7.8" r=".95" fill="#fff"/>',
  ht: '<rect width="30" height="20" fill="#D21034"/><rect width="30" height="10" fill="#00209F"/><rect x="11" y="7" width="8" height="6" fill="#fff"/><path d="M15 8.2 L16.8 11.5 H13.2 Z" fill="#228B22"/>',
  py: '<rect width="30" height="20" fill="#0038A8"/><rect width="30" height="6.67" fill="#D52B1E"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><circle cx="15" cy="10" r="2" fill="#F6C400" stroke="#0038A8" stroke-width=".45"/>',
  ba: '<rect width="30" height="20" fill="#002395"/><path d="M12 0 H30 V20 Z" fill="#FECB00"/>',
  sco: '<rect width="30" height="20" fill="#005EB8"/><path d="M0 0 L30 20 M30 0 L0 20" stroke="#fff" stroke-width="4"/>',
  tr: '<rect width="30" height="20" fill="#E30A17"/><circle cx="12" cy="10" r="4.5" fill="#fff"/><circle cx="13.3" cy="10" r="3.6" fill="#E30A17"/><path d="M18 7.2 L18.8 9.3 H21 L19.2 10.6 L19.9 12.8 L18 11.4 L16.1 12.8 L16.8 10.6 L15 9.3 H17.2 Z" fill="#fff"/>',
};

// Team display name → FLAGS key. Covers the 48-team tournament field.
const TEAM_FLAG_CODE: Record<string, string> = {
  Algeria: "dz",
  Argentina: "ar",
  Australia: "au",
  Austria: "at",
  Belgium: "be",
  "Bosnia & Herzegovina": "ba",
  Brazil: "br",
  Canada: "ca",
  "Cape Verde Islands": "cv",
  Colombia: "co",
  "Congo DR": "cd",
  Croatia: "hr",
  "Curaçao": "cw",
  Czechia: "cz",
  Ecuador: "ec",
  Egypt: "eg",
  England: "eng",
  France: "fr",
  Germany: "de",
  Ghana: "gh",
  Haiti: "ht",
  Iran: "ir",
  Iraq: "iq",
  "Ivory Coast": "ci",
  Japan: "jp",
  Jordan: "jo",
  Mexico: "mx",
  Morocco: "ma",
  Netherlands: "nl",
  "New Zealand": "nz",
  Norway: "no",
  Panama: "pa",
  Paraguay: "py",
  Portugal: "pt",
  Qatar: "qa",
  "Saudi Arabia": "sa",
  Scotland: "sco",
  Senegal: "sn",
  "South Africa": "za",
  "South Korea": "kr",
  Spain: "es",
  Sweden: "se",
  Switzerland: "ch",
  Tunisia: "tn",
  "Türkiye": "tr",
  USA: "us",
  Uruguay: "uy",
  Uzbekistan: "uz",
};

export function flagSvg(team: string | null): string | null {
  if (!team) return null;
  const code = TEAM_FLAG_CODE[team.trim()];
  return code ? (FLAGS[code] ?? null) : null;
}

function hexLuminance(hex: string): number {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// Representative team color for an avatar badge: the flag's first saturated
// fill (skips near-white/near-black bands so e.g. Serbia reads red, not white).
export function flagPrimaryColor(team: string | null): string | null {
  const svg = flagSvg(team);
  if (!svg) return null;
  const fills = [...svg.matchAll(/fill="(#[0-9a-fA-F]{3,6})"/g)].map((m) => m[1]);
  for (const hex of fills) {
    const lum = hexLuminance(hex);
    if (lum > 235 || lum < 25) continue;
    return hex;
  }
  return fills[0] ?? null;
}

// Readable initials color for a colored avatar background.
export function avatarTextColor(bgHex: string): string {
  return hexLuminance(bgHex) > 150 ? "#0B1020" : "#fff";
}
