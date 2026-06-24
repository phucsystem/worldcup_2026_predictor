/*
  CJX entrance animations + light interactivity
  Source: docs/UI_SPEC.md §1 CJX, §3 Standings (view toggle)
*/

/* CJX entrance animations injected per body class (respects reduced-motion via CSS) */
(function injectCjxAnimations() {
  const css = `
    .cjx-discovery [data-cjx-entrance] { animation: fadeInUp 0.8s ease-out; }
    .cjx-onboarding [data-cjx-entrance] { animation: fadeInUp 0.6s ease-out; }
    .cjx-usage [data-cjx-entrance] { animation: fadeIn 0.3s ease; }
    .cjx-retention [data-cjx-entrance] { animation: fadeIn 0.4s ease; }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);
})();

/* Inline SVG flags — single source of truth, injected into [data-flag].
   Simplified geometric flags (emblems approximated) so they stay self-contained,
   crisp, and identical across operating systems (unlike regional-indicator emoji). */
const FLAGS = {
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
  us: '<rect width="30" height="20" fill="#B22234"/><path d="M0 2.85 H30 M0 5.7 H30 M0 8.55 H30 M0 11.4 H30 M0 14.25 H30 M0 17.1 H30" stroke="#fff" stroke-width="1.42"/><rect width="13" height="10.8" fill="#3C3B6E"/><g fill="#fff"><circle cx="2.1" cy="2" r=".45"/><circle cx="5" cy="2" r=".45"/><circle cx="7.9" cy="2" r=".45"/><circle cx="10.8" cy="2" r=".45"/><circle cx="3.6" cy="4.5" r=".45"/><circle cx="6.5" cy="4.5" r=".45"/><circle cx="9.4" cy="4.5" r=".45"/><circle cx="2.1" cy="7" r=".45"/><circle cx="5" cy="7" r=".45"/><circle cx="7.9" cy="7" r=".45"/><circle cx="10.8" cy="7" r=".45"/></g>',
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
  uz: '<rect width="30" height="20" fill="#1EB53A"/><rect width="30" height="9" fill="#0099B5"/><rect y="9" width="30" height="2" fill="#CE1126"/><rect y="11" width="30" height="5" fill="#fff"/><circle cx="5.5" cy="4.5" r="2.2" fill="#fff"/><circle cx="6.2" cy="4.5" r="2.2" fill="#0099B5"/><g fill="#fff"><circle cx="11" cy="2.5" r=".45"/><circle cx="13" cy="2.5" r=".45"/><circle cx="15" cy="2.5" r=".45"/><circle cx="12" cy="4.6" r=".45"/><circle cx="14" cy="4.6" r=".45"/><circle cx="16" cy="4.6" r=".45"/></g>',
  cv: '<rect width="30" height="20" fill="#003893"/><rect y="11" width="30" height="3" fill="#fff"/><rect y="12" width="30" height="1" fill="#CF2027"/><g fill="#F7D116"><circle cx="9" cy="9" r=".55"/><circle cx="11" cy="8" r=".55"/><circle cx="13" cy="9" r=".55"/><circle cx="14" cy="11" r=".55"/><circle cx="13" cy="13" r=".55"/><circle cx="11" cy="14" r=".55"/><circle cx="9" cy="13" r=".55"/><circle cx="8" cy="11" r=".55"/></g>',
  cd: '<rect width="30" height="20" fill="#007FFF"/><path d="M-2 20 L30 -2" stroke="#F7D618" stroke-width="6"/><path d="M-2 20 L30 -2" stroke="#CE1021" stroke-width="3"/><path d="M6 2 L7.1 5.3 H10.5 L7.7 7.3 L8.8 10.5 L6 8.5 L3.2 10.5 L4.3 7.3 L1.5 5.3 H4.9 Z" fill="#F7D618"/>',
  cw: '<rect width="30" height="20" fill="#002B7F"/><rect y="13" width="30" height="2.2" fill="#F9E814"/><circle cx="7.5" cy="5.5" r="1.4" fill="#fff"/><circle cx="11" cy="7.8" r=".95" fill="#fff"/>',
  ht: '<rect width="30" height="20" fill="#D21034"/><rect width="30" height="10" fill="#00209F"/><rect x="11" y="7" width="8" height="6" fill="#fff"/><path d="M15 8.2 L16.8 11.5 H13.2 Z" fill="#228B22"/>',
  py: '<rect width="30" height="20" fill="#0038A8"/><rect width="30" height="6.67" fill="#D52B1E"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><circle cx="15" cy="10" r="2" fill="#F6C400" stroke="#0038A8" stroke-width=".45"/>',
  ba: '<rect width="30" height="20" fill="#002395"/><path d="M12 0 H30 V20 Z" fill="#FECB00"/><g fill="#fff"><circle cx="10" cy="2" r=".65"/><circle cx="12.5" cy="4.5" r=".65"/><circle cx="15" cy="7" r=".65"/><circle cx="17.5" cy="9.5" r=".65"/><circle cx="20" cy="12" r=".65"/><circle cx="22.5" cy="14.5" r=".65"/><circle cx="25" cy="17" r=".65"/></g>',
  sco: '<rect width="30" height="20" fill="#005EB8"/><path d="M0 0 L30 20 M30 0 L0 20" stroke="#fff" stroke-width="4"/>',
  tr: '<rect width="30" height="20" fill="#E30A17"/><circle cx="12" cy="10" r="4.5" fill="#fff"/><circle cx="13.3" cy="10" r="3.6" fill="#E30A17"/><path d="M18 7.2 L18.8 9.3 H21 L19.2 10.6 L19.9 12.8 L18 11.4 L16.1 12.8 L16.8 10.6 L15 9.3 H17.2 Z" fill="#fff"/>'
};

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.flag[data-flag]').forEach(function (el) {
    const code = el.dataset.flag;
    const label = el.dataset.code || code.toUpperCase();
    if (FLAGS[code]) {
      el.innerHTML = '<svg viewBox="0 0 30 20" class="flag-svg" role="img" aria-label="' + label + ' flag">' + FLAGS[code] + '</svg>';
    } else {
      // crest fallback for any team without a built flag
      el.outerHTML = '<span class="' + el.className + ' crest" style="background:' + (el.dataset.color || '#1e3157') + '">' + label + '</span>';
    }
  });

  /* Faded two-team flag backdrop, reused for both a match hero and the whole page.
     - data-flag-bg        → inset layer inside a positioned container (the hero)
     - data-flag-bg-page   → fixed, full-viewport layer behind all page content
     Both read data-home/data-away (FIFA codes): home flag fills the left, away the
     right, with a dark tint over the top for readability. */
  function buildFlagLayer(home, away, className, host, prepend) {
    if (!FLAGS[home] && !FLAGS[away]) return;
    function panel(code, side) {
      if (!FLAGS[code]) return '';
      return '<div class="flag-bg-half ' + side + '"><svg viewBox="0 0 30 20" preserveAspectRatio="xMidYMid slice">' + FLAGS[code] + '</svg></div>';
    }
    const wrap = document.createElement('div');
    wrap.className = className;
    wrap.setAttribute('aria-hidden', 'true');
    wrap.innerHTML = panel(home, 'home') + panel(away, 'away') + '<div class="flag-bg-tint"></div>';
    host.insertBefore(wrap, prepend ? host.firstChild : null);
  }
  document.querySelectorAll('[data-flag-bg]').forEach(function (el) {
    buildFlagLayer(el.dataset.home, el.dataset.away, 'flag-bg', el, true);
  });
  document.querySelectorAll('[data-flag-bg-page]').forEach(function (el) {
    buildFlagLayer(el.dataset.home, el.dataset.away, 'page-flag-bg', document.body, true);
  });
});

/* Live countdown clocks for upcoming matches.
   Targets are derived from data-offset-min at page load (minutes from now), so the
   prototype always shows a realistic ticking countdown regardless of when it's opened.
   In production, swap to an absolute data-kickoff ISO timestamp. */
(function initCountdowns() {
  const els = Array.prototype.slice.call(document.querySelectorAll('[data-countdown]'));
  if (!els.length) return;

  const now0 = Date.now();
  els.forEach(function (el) {
    const off = parseInt(el.dataset.offsetMin || '0', 10);
    el.dataset.target = String(now0 + off * 60000);
    el.setAttribute('aria-hidden', 'true'); // ticking text would spam screen readers; static kickoff label carries the time
  });

  function pad(n) { return n < 10 ? '0' + n : String(n); }
  function seg(num, lbl) {
    return '<span class="cd-seg"><span class="cd-num">' + pad(num) + '</span><span class="cd-lbl">' + lbl + '</span></span>';
  }

  function tick() {
    const now = Date.now();
    els.forEach(function (el) {
      let s = Math.floor((parseInt(el.dataset.target, 10) - now) / 1000);
      if (s <= 0) {
        el.innerHTML = '<span class="cd-live">LIVE</span>';
        return;
      }
      const d = Math.floor(s / 86400); s %= 86400;
      const h = Math.floor(s / 3600); s %= 3600;
      const m = Math.floor(s / 60);
      const sec = s % 60;
      if (el.dataset.cd === 'inline') {
        el.textContent = 'in ' + (d ? d + 'd ' : '') + h + 'h ' + pad(m) + 'm ' + pad(sec) + 's';
      } else {
        el.innerHTML = (d ? seg(d, 'days') : '') + seg(h, 'hrs') + seg(m, 'min') + seg(sec, 'sec');
      }
    });
  }
  tick();
  setInterval(tick, 1000);
})();

/* Live match-minute ticker for in-progress fixtures (cosmetic in the prototype). */
(function initLiveClocks() {
  const els = Array.prototype.slice.call(document.querySelectorAll('[data-live-min]'));
  if (!els.length) return;
  els.forEach(function (el) {
    let min = parseInt(el.dataset.liveMin || '0', 10);
    const out = el.querySelector('.lc-min');
    if (!out) return;
    setInterval(function () {
      if (min >= 90) return;
      min += 1;
      out.textContent = String(min);
    }, 20000);
  });
})();

/* Knockout bracket: hover a match to trace its winner's path to the final.
   Match ids are read from each card's label (e.g. "R16-1 · 28 Jun" -> "R16-1"). */
(function initBracketPath() {
  const matches = Array.prototype.slice.call(document.querySelectorAll('.bracket-match'));
  if (!matches.length) return;

  const FEEDS = {
    'R16-1': 'QF1', 'R16-2': 'QF1', 'R16-3': 'QF2', 'R16-4': 'QF2',
    'R16-5': 'QF3', 'R16-6': 'QF3', 'R16-7': 'QF4', 'R16-8': 'QF4',
    'QF1': 'SF1', 'QF2': 'SF1', 'QF3': 'SF2', 'QF4': 'SF2',
    'SF1': 'Final', 'SF2': 'Final'
  };

  const byId = {};
  const bracket = document.querySelector('.bracket');
  matches.forEach(function (m) {
    const lbl = m.querySelector('.bracket-card-label');
    if (!lbl) return;
    const id = lbl.textContent.trim().split(' ')[0];
    m.dataset.mid = id;
    byId[id] = m;
  });

  matches.forEach(function (m) {
    m.addEventListener('mouseenter', function () {
      if (bracket) bracket.classList.add('dimmed');
      let cur = m, guard = 0;
      while (cur && guard++ < 12) {
        cur.classList.add('path');
        const next = FEEDS[cur.dataset.mid];
        cur = next ? byId[next] : null;
      }
    });
    m.addEventListener('mouseleave', function () {
      if (bracket) bracket.classList.remove('dimmed');
      matches.forEach(function (x) { x.classList.remove('path'); });
    });
  });
})();

/* S-01 Latest Results: "Display in Groups" toggle. */
document.addEventListener('DOMContentLoaded', function () {
  const widget = document.querySelector('[data-rw]');
  if (!widget) return;
  const input = widget.querySelector('[data-rw-toggle]');
  const stateLbl = widget.querySelector('.rw-tg-state');
  const list = widget.querySelector('.rw-list');
  if (!input || !list) return;

  const rows = Array.prototype.slice.call(list.querySelectorAll('.match-row'));
  const groupHeaders = Array.prototype.slice.call(list.querySelectorAll('.rw-group-header'));
  const monthRank = {
    January: 1,
    February: 2,
    March: 3,
    April: 4,
    May: 5,
    June: 6,
    July: 7,
    August: 8,
    September: 9,
    October: 10,
    November: 11,
    December: 12
  };

  function getDateRank(dateLabel) {
    const dateParts = dateLabel.replace(',', '').split(' ');
    const day = Number(dateParts[1] || 0);
    const month = monthRank[dateParts[2]] || 0;
    return 20260000 + month * 100 + day;
  }

  const groups = [];
  rows.forEach(function (row) {
    if (groups.indexOf(row.dataset.group) === -1) groups.push(row.dataset.group);
  });

  groups.sort(function (firstGroup, secondGroup) {
    const firstLatestDate = Math.max.apply(null, rows
      .filter(function (row) { return row.dataset.group === firstGroup; })
      .map(function (row) { return getDateRank(row.dataset.date); }));
    const secondLatestDate = Math.max.apply(null, rows
      .filter(function (row) { return row.dataset.group === secondGroup; })
      .map(function (row) { return getDateRank(row.dataset.date); }));
    return secondLatestDate - firstLatestDate || firstGroup.localeCompare(secondGroup);
  });

  const dates = [];
  rows.forEach(function (row) {
    if (dates.indexOf(row.dataset.date) === -1) dates.push(row.dataset.date);
  });
  dates.sort(function (firstDate, secondDate) {
    return getDateRank(secondDate) - getDateRank(firstDate);
  });

  function accuracyTier(pct) {
    if (pct >= 67) return 'high';
    if (pct >= 34) return 'mid';
    return 'low';
  }

  function matchSummary(row) {
    const names = row.querySelectorAll('.mr-name');
    const scores = row.querySelectorAll('.mr-score');
    return {
      home: names[0] ? names[0].textContent : '',
      away: names[1] ? names[1].textContent : '',
      homeScore: scores[0] ? scores[0].textContent : '',
      awayScore: scores[1] ? scores[1].textContent : '',
      hit: row.dataset.forecast === 'hit',
    };
  }

  const dateHeaders = dates.map(function (dateLabel) {
    const dateHeader = document.createElement('div');
    dateHeader.className = 'rw-date-header';
    dateHeader.dataset.date = dateLabel;

    const label = document.createElement('span');
    label.className = 'rw-dh-label';
    label.textContent = dateLabel;
    dateHeader.appendChild(label);

    // Forecast accuracy = correct forecasts / matches that carried a forecast.
    const forecasted = rows.filter(function (row) {
      return row.dataset.date === dateLabel && row.dataset.forecast;
    });
    if (!forecasted.length) {
      list.appendChild(dateHeader);
      return dateHeader;
    }

    const hits = forecasted.filter(function (row) {
      return row.dataset.forecast === 'hit';
    }).length;
    const pct = Math.round((hits / forecasted.length) * 100);
    const tier = accuracyTier(pct);

    const wrap = document.createElement('span');
    wrap.className = 'rw-dh-acc-wrap';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'rw-dh-acc acc-' + tier;
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute(
      'aria-label',
      'Model forecast ' + hits + ' of ' + forecasted.length +
        ' results correctly on ' + dateLabel + '. Show breakdown.'
    );
    btn.innerHTML =
      '<span class="rw-dh-acc-icon" aria-hidden="true">◎</span>' +
      '<span class="rw-dh-acc-frac">' + hits + '/' + forecasted.length + '</span>' +
      '<span class="rw-dh-acc-pct">' + pct + '%</span>';
    wrap.appendChild(btn);

    const pop = document.createElement('div');
    pop.className = 'rw-dh-pop';
    pop.setAttribute('role', 'dialog');
    pop.setAttribute('aria-label', 'Forecast summary for ' + dateLabel);
    pop.hidden = true;
    let itemsHtml = '';
    forecasted.forEach(function (row) {
      const m = matchSummary(row);
      itemsHtml +=
        '<li class="rw-dh-pop-item ' + (m.hit ? 'hit' : 'miss') + '">' +
        '<span class="rw-dh-pop-mark" aria-hidden="true">' + (m.hit ? '✓' : '✗') + '</span>' +
        '<span class="rw-dh-pop-match">' + m.home + ' ' + m.homeScore + '–' + m.awayScore + ' ' + m.away + '</span>' +
        '<span class="rw-dh-pop-verdict">' + (m.hit ? 'Called' : 'Missed') + '</span>' +
        '</li>';
    });
    pop.innerHTML =
      '<div class="rw-dh-pop-head">' +
      '<span class="rw-dh-pop-title">Forecast · ' + dateLabel + '</span>' +
      '<span class="rw-dh-pop-rate acc-' + tier + '">' + hits + '/' + forecasted.length + ' correct · ' + pct + '%</span>' +
      '</div>' +
      '<ul class="rw-dh-pop-list">' + itemsHtml + '</ul>';
    wrap.appendChild(pop);

    let pinned = false;
    function setOpen(open) {
      pop.hidden = !open;
      btn.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    btn.addEventListener('mouseenter', function () { if (!pinned) setOpen(true); });
    btn.addEventListener('mouseleave', function () { if (!pinned) setOpen(false); });
    btn.addEventListener('focus', function () { if (!pinned) setOpen(true); });
    btn.addEventListener('blur', function () { if (!pinned) setOpen(false); });
    btn.addEventListener('click', function (event) {
      event.preventDefault();
      pinned = !pinned;
      setOpen(pinned);
    });
    document.addEventListener('click', function (event) {
      if (pinned && !wrap.contains(event.target)) { pinned = false; setOpen(false); }
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && pinned) { pinned = false; setOpen(false); }
    });

    dateHeader.appendChild(wrap);
    list.appendChild(dateHeader);
    return dateHeader;
  });

  function apply() {
    widget.classList.toggle('grouped', input.checked);
    widget.classList.toggle('has-date-headers', !input.checked);
    if (stateLbl) stateLbl.textContent = input.checked ? 'On' : 'Off';

    if (input.checked) {
      groupHeaders.forEach(function (groupHeader) {
        groupHeader.style.order = groups.indexOf(groupHeader.dataset.group) * 100;
      });
      const groupCounters = {};
      rows
        .slice()
        .sort(function (firstRow, secondRow) {
          return getDateRank(secondRow.dataset.date) - getDateRank(firstRow.dataset.date);
        })
        .forEach(function (row) {
          const groupIndex = groups.indexOf(row.dataset.group);
          groupCounters[groupIndex] = (groupCounters[groupIndex] || 0) + 1;
          row.style.order = groupIndex * 100 + groupCounters[groupIndex];
        });
      return;
    }

    dateHeaders.forEach(function (dateHeader) {
      dateHeader.style.order = dates.indexOf(dateHeader.dataset.date) * 100;
    });
    const dateCounters = {};
    rows
      .slice()
      .sort(function (firstRow, secondRow) {
        const dateDiff = getDateRank(secondRow.dataset.date) - getDateRank(firstRow.dataset.date);
        return dateDiff || firstRow.dataset.group.localeCompare(secondRow.dataset.group);
      })
      .forEach(function (row) {
        const dateIndex = dates.indexOf(row.dataset.date);
        dateCounters[dateIndex] = (dateCounters[dateIndex] || 0) + 1;
        row.style.order = dateIndex * 100 + dateCounters[dateIndex];
      });
  }
  input.addEventListener('change', apply);
  apply();
});

/* S-03 Standings: groups <-> knockout segmented toggle */
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.querySelector('[data-view-toggle]');
  if (!toggle) return;

  const buttons = toggle.querySelectorAll('.toggle-btn');
  const panels = document.querySelectorAll('[data-view-panel]');

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const target = btn.dataset.view;
      buttons.forEach((b) => b.classList.toggle('active', b === btn));
      panels.forEach(function (panel) {
        panel.hidden = panel.dataset.viewPanel !== target;
      });
    });
  });
});

/* S-09 System Logs: filter + search + expand + live-tail + pagination (50/page) */
document.addEventListener('DOMContentLoaded', function () {
  const console_ = document.querySelector('[data-log-console]');
  if (!console_) return;

  const PAGE_SIZE = 50;
  const tbody = console_.querySelector('tbody');
  const filterBtns = document.querySelectorAll('[data-log-filter] .toggle-btn');
  const search = document.querySelector('[data-log-search]');
  const noResults = console_.querySelector('.log-noresults');
  const pager = document.querySelector('[data-log-pagination]');

  /* --- Synthesize a realistic backlog so 50/page pagination is demonstrable.
     Curated rows (with tracebacks) stay newest; filler extends further back. --- */
  const ICONS = {
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
    warn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
  };
  const LABEL = { info: 'Info', warn: 'Warn' };
  const POOL = [
    ['info', 'pipeline.run', 'Pipeline run finished — brief stored (3 articles)'],
    ['info', 'pipeline.run', 'Analyst node complete — 4 articles drafted'],
    ['info', 'pipeline.run', 'Collector node complete — 12 fixtures, 6 standings groups (1.7s)'],
    ['info', 'data.collect', 'Fetched 12 fixtures from API-Football (group stage, season 2026)'],
    ['info', 'data.collect', 'Standings recomputed for 6 groups (deterministic)'],
    ['info', 'data.collect', 'No fixture changes since last poll — skipping write'],
    ['info', 'data.collect', 'Persisted matchday snapshot (48 rows)'],
    ['info', 'pipeline.scheduler_entry', 'Scheduler tick — starting refresh run (interval 30m)'],
    ['info', 'pipeline.scheduler_entry', 'Scheduler idle — next run in 30m'],
    ['warn', 'data.collect', 'API-Football response slow (3.1s) — within retry budget'],
    ['warn', 'pipeline.run', 'DeepSeek response missing usage_metadata — cost estimate skipped']
  ];
  const NOW = 3 * 3600 + 42 * 60; // 03:42:00 reference for relative labels
  function fmt(sec) {
    const s = ((sec % 86400) + 86400) % 86400;
    const p = (n) => String(n).padStart(2, '0');
    return p(Math.floor(s / 3600)) + ':' + p(Math.floor((s % 3600) / 60)) + ':' + p(s % 60);
  }
  function rel(sec) {
    const ago = Math.max(60, NOW - sec);
    return ago < 3600 ? Math.round(ago / 60) + 'm ago' : Math.round(ago / 3600) + 'h ago';
  }
  let cursor = 3 * 3600 + 9 * 60; // first filler just before the oldest curated row (03:10)
  const filler = [];
  for (let i = 0; i < 112; i++) {
    cursor -= 40 + (i * 37) % 170; // deterministic 40–210s gaps
    const [lvl, src, msg] = POOL[(i * 7 + 3) % POOL.length];
    filler.push(
      '<tr class="log-row" data-level="' + lvl + '">' +
        '<td class="c-time"><span class="log-time">' + fmt(cursor) + '<span class="lt-rel">' + rel(cursor) + '</span></span></td>' +
        '<td class="c-level"><span class="lvl ' + lvl + '">' + ICONS[lvl] + LABEL[lvl] + '</span></td>' +
        '<td class="c-source"><span class="log-source">' + src + '</span></td>' +
        '<td class="c-msg log-msg-cell"><span class="log-msg">' + msg + '</span></td>' +
      '</tr>'
    );
  }
  tbody.insertAdjacentHTML('beforeend', filler.join(''));

  const rows = Array.prototype.slice.call(console_.querySelectorAll('tr.log-row'));
  let level = 'all';
  let term = '';
  let page = 1;

  function render() {
    const matched = rows.filter(function (row) {
      const okLevel = level === 'all' || row.dataset.level === level;
      const okTerm = !term || row.textContent.toLowerCase().indexOf(term) !== -1;
      return okLevel && okTerm;
    });
    const pageCount = Math.max(1, Math.ceil(matched.length / PAGE_SIZE));
    if (page > pageCount) page = pageCount;
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const matchedSet = new Set(matched);

    rows.forEach(function (row) {
      const idx = matched.indexOf(row);
      const onPage = matchedSet.has(row) && idx >= start && idx < end;
      row.hidden = !onPage;
      const detail = row.nextElementSibling;
      if (detail && detail.classList.contains('log-detail-row')) {
        detail.hidden = !onPage || row.dataset.expanded !== 'true';
      }
    });

    if (noResults) noResults.hidden = matched.length !== 0;
    renderPager(matched.length, pageCount, start);
  }

  function renderPager(total, pageCount, start) {
    if (!pager) return;
    if (total === 0) { pager.hidden = true; return; }
    pager.hidden = false;
    const from = start + 1;
    const to = Math.min(start + PAGE_SIZE, total);
    let nums = '';
    for (let p = 1; p <= pageCount; p++) {
      nums += '<button class="log-page-btn' + (p === page ? ' active' : '') +
        '" data-page="' + p + '" aria-current="' + (p === page ? 'page' : 'false') + '">' + p + '</button>';
    }
    pager.innerHTML =
      '<span class="log-page-range">' + from + '–' + to + ' of ' + total + '</span>' +
      '<div class="log-page-controls">' +
        '<button class="log-page-btn nav" data-page="prev"' + (page === 1 ? ' disabled' : '') + ' aria-label="Previous page">Prev</button>' +
        nums +
        '<button class="log-page-btn nav" data-page="next"' + (page === pageCount ? ' disabled' : '') + ' aria-label="Next page">Next</button>' +
      '</div>';
  }

  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      level = btn.dataset.level;
      page = 1;
      filterBtns.forEach((b) => b.classList.toggle('active', b === btn));
      render();
    });
  });

  if (search) {
    search.addEventListener('input', function () {
      term = search.value.trim().toLowerCase();
      page = 1;
      render();
    });
  }

  if (pager) {
    pager.addEventListener('click', function (e) {
      const btn = e.target.closest('.log-page-btn');
      if (!btn || btn.disabled) return;
      const target = btn.dataset.page;
      if (target === 'prev') page = Math.max(1, page - 1);
      else if (target === 'next') page += 1;
      else page = parseInt(target, 10);
      render();
      console_.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  // Expand / collapse detail (traceback, run context) — curated rows only
  console_.querySelectorAll('.log-expand').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const row = btn.closest('tr.log-row');
      const detail = row.nextElementSibling;
      if (!detail || !detail.classList.contains('log-detail-row')) return;
      const open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open));
      row.dataset.expanded = String(!open);
      detail.hidden = open;
    });
  });

  // Live-tail toggle (purely visual in the prototype — pulses the dot)
  const tail = document.querySelector('[data-log-tail]');
  if (tail) {
    tail.addEventListener('click', function () {
      const on = tail.getAttribute('aria-pressed') === 'true';
      tail.setAttribute('aria-pressed', String(!on));
      tail.querySelector('.lt-label').textContent = on ? 'Paused' : 'Live';
    });
  }

  render();
});

/* ====================================================================
   Supporter feedback bot (S-12) + Admin feedback triage (S-14)
   Original host-nation supporter characters (moose/jaguar/eagle).
   ==================================================================== */
(function () {
  // --- Mascot SVGs (original art; NOT the trademarked FIFA 2026 mascots) ---
  const MASCOTS = {
    moose:
      '<svg viewBox="0 0 48 48" aria-hidden="true">' +
      '<path d="M16 13 Q9 6 5 9 Q11 9 12 13 Q7 11 6 15 Q12 13 15 16Z" fill="#8a5a2b"/>' +
      '<path d="M32 13 Q39 6 43 9 Q37 9 36 13 Q41 11 42 15 Q36 13 33 16Z" fill="#8a5a2b"/>' +
      '<ellipse cx="13" cy="20" rx="3.4" ry="5" fill="#6a3f22"/><ellipse cx="35" cy="20" rx="3.4" ry="5" fill="#6a3f22"/>' +
      '<ellipse cx="24" cy="26" rx="12" ry="13" fill="#7a4a28"/>' +
      '<ellipse cx="24" cy="33" rx="8" ry="7" fill="#9a6638"/>' +
      '<ellipse cx="24" cy="33.5" rx="3.4" ry="2.5" fill="#33200f"/>' +
      '<circle cx="19" cy="24" r="2.2" fill="#1a0f08"/><circle cx="29" cy="24" r="2.2" fill="#1a0f08"/>' +
      '<circle cx="19.7" cy="23.3" r="0.8" fill="#fff"/><circle cx="29.7" cy="23.3" r="0.8" fill="#fff"/>' +
      '<circle cx="14" cy="30" r="2" fill="#D80621" opacity="0.5"/><circle cx="34" cy="30" r="2" fill="#D80621" opacity="0.5"/>' +
      '</svg>',
    jaguar:
      '<svg viewBox="0 0 48 48" aria-hidden="true">' +
      '<path d="M12 13 L19 20 L10 22Z" fill="#c98a2e"/><path d="M36 13 L29 20 L38 22Z" fill="#c98a2e"/>' +
      '<path d="M13 16 L17 20 L12 21Z" fill="#5a3a12"/><path d="M35 16 L31 20 L36 21Z" fill="#5a3a12"/>' +
      '<ellipse cx="24" cy="26" rx="13" ry="12" fill="#e0a93f"/>' +
      '<circle cx="14" cy="22" r="1.5" fill="#5a3a12"/><circle cx="34" cy="22" r="1.5" fill="#5a3a12"/>' +
      '<circle cx="12.5" cy="29" r="1.2" fill="#5a3a12"/><circle cx="35.5" cy="29" r="1.2" fill="#5a3a12"/>' +
      '<ellipse cx="24" cy="31" rx="8" ry="6" fill="#f3d79a"/>' +
      '<circle cx="19" cy="24" r="2.4" fill="#1c3a1c"/><circle cx="29" cy="24" r="2.4" fill="#1c3a1c"/>' +
      '<circle cx="19.8" cy="23.2" r="0.8" fill="#fff"/><circle cx="29.8" cy="23.2" r="0.8" fill="#fff"/>' +
      '<path d="M21.5 29 L26.5 29 L24 31.6Z" fill="#2BD37E"/>' +
      '</svg>',
    eagle:
      '<svg viewBox="0 0 48 48" aria-hidden="true">' +
      '<path d="M11 18 Q14 11 18 16 Q20 10 24 15 Q28 10 30 16 Q34 11 37 18Z" fill="#dfe7f5"/>' +
      '<ellipse cx="24" cy="24" rx="13" ry="13" fill="#f4f7ff"/>' +
      '<path d="M13 21 Q19 18 23 22.5" stroke="#1b3a6b" stroke-width="2.4" fill="none" stroke-linecap="round"/>' +
      '<path d="M35 21 Q29 18 25 22.5" stroke="#1b3a6b" stroke-width="2.4" fill="none" stroke-linecap="round"/>' +
      '<circle cx="18" cy="24.5" r="2.4" fill="#15233f"/><circle cx="30" cy="24.5" r="2.4" fill="#15233f"/>' +
      '<circle cx="18.8" cy="23.7" r="0.8" fill="#fff"/><circle cx="30.8" cy="23.7" r="0.8" fill="#fff"/>' +
      '<path d="M21 28 L27 28 L24 37 Q22.5 33 21 28Z" fill="#F4B740"/>' +
      '<path d="M21 28 L27 28 L24 30.5Z" fill="#d99a1f"/>' +
      '<circle cx="12.5" cy="28" r="1.9" fill="#2D6BF6" opacity="0.45"/><circle cx="35.5" cy="28" r="1.9" fill="#2D6BF6" opacity="0.45"/>' +
      '</svg>',
  };
  const ORDER = ['moose', 'jaguar', 'eagle'];

  function renderMascots(root) {
    (root || document).querySelectorAll('[data-mascot]').forEach(function (el) {
      if (el.dataset.rendered) return;
      const kind = el.dataset.mascot;
      el.innerHTML = MASCOTS[kind] || MASCOTS.moose;
      if (!el.classList.contains(kind)) el.classList.add(kind);
      el.dataset.rendered = '1';
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    renderMascots();

    /* ---- S-12 supporter feedback widget ---- */
    const fab = document.querySelector('[data-fb-fab]');
    const panel = document.querySelector('[data-fb-panel]');
    if (fab && panel) {
      const body = panel.querySelector('[data-fb-body]');
      const composer = panel.querySelector('[data-fb-composer]');
      const input = panel.querySelector('.fb-input');
      const sendBtn = panel.querySelector('.fb-send');
      let turn = 0; // 0 = greeting, 1 = picked a topic

      function open() { panel.hidden = false; fab.setAttribute('aria-expanded', 'true'); if (input) input.focus(); }
      function close() { panel.hidden = true; fab.setAttribute('aria-expanded', 'false'); }
      fab.addEventListener('click', function () { panel.hidden ? open() : close(); });
      panel.querySelectorAll('[data-fb-close]').forEach(function (b) { b.addEventListener('click', close); });

      function addBubble(side, text, mascot) {
        const row = document.createElement('div');
        row.className = 'fb-msg ' + side;
        if (side === 'bot') {
          const av = document.createElement('span');
          av.className = 'mascot-av ' + (mascot || 'moose');
          av.dataset.mascot = mascot || 'moose';
          row.appendChild(av);
        }
        const bubble = document.createElement('div');
        bubble.className = 'fb-bubble';
        bubble.textContent = text;
        row.appendChild(bubble);
        body.insertBefore(row, body.querySelector('[data-fb-prompts]') || null);
        renderMascots(row);
        body.scrollTop = body.scrollHeight;
      }

      function botFollowUp(topic) {
        const lines = {
          bug: "Oh no — what broke? Tell me what you saw and where.",
          feature: "Love it! What would make the platform better for you?",
          other: "Go ahead — I'm all ears (well, antlers).",
        };
        const prompts = panel.querySelector('[data-fb-prompts]');
        if (prompts) prompts.remove();
        addBubble('bot', lines[topic] || lines.other, ORDER[turn % 3]);
        turn = 1;
        if (composer) composer.hidden = false;
        if (input) input.focus();
      }

      panel.querySelectorAll('[data-fb-prompt]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          addBubble('user', btn.textContent.trim());
          botFollowUp(btn.dataset.fbPrompt);
        });
      });

      function celebrate() {
        const colors = ['#FCDD09', '#2BD37E', '#4D8BFF', '#FF5A5A', '#F4B740'];
        const wrap = document.createElement('div');
        wrap.className = 'fb-confetti';
        for (let i = 0; i < 16; i++) {
          const c = document.createElement('i');
          c.style.left = (6 + Math.random() * 88) + '%';
          c.style.background = colors[i % colors.length];
          c.style.animationDelay = (Math.random() * 0.25) + 's';
          c.style.transform = 'rotate(' + (Math.random() * 90) + 'deg)';
          wrap.appendChild(c);
        }
        panel.appendChild(wrap);
        setTimeout(function () { wrap.remove(); }, 1300);
      }

      function submit() {
        const text = (input.value || '').trim();
        if (!text) return;
        // In production this POSTs to /api/feedback (page URL captured server-side).
        body.innerHTML =
          '<div class="fb-thanks">' +
          '<span class="mascot-av lg ' + ORDER[turn % 3] + '" data-mascot="' + ORDER[turn % 3] + '"></span>' +
          '<h3>Thank you! 🎉</h3>' +
          '<p>Your feedback is in. The supporters are on it.</p>' +
          '</div>';
        renderMascots(body);
        if (composer) composer.hidden = true;
        celebrate();
      }
      if (sendBtn) sendBtn.addEventListener('click', submit);
      if (input) input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
      });
    }

    /* ---- S-14 admin: tabs, filter, feedback status triage ---- */
    const admin = document.querySelector('[data-admin-feedback]');
    if (admin) {
      // tab switching
      admin.querySelectorAll('[data-admin-tab]').forEach(function (tab) {
        tab.addEventListener('click', function () {
          const name = tab.dataset.adminTab;
          admin.querySelectorAll('[data-admin-tab]').forEach(function (t) { t.classList.toggle('active', t === tab); });
          admin.querySelectorAll('[data-admin-panel]').forEach(function (p) {
            p.hidden = p.dataset.adminPanel !== name;
          });
        });
      });

      const list = admin.querySelector('[data-fb-list]');
      const emptyState = admin.querySelector('[data-fb-empty]');
      const labels = { new: 'New', done: 'Done', wont: "Won't do" };
      let currentFilter = 'all';

      function items() { return list ? Array.prototype.slice.call(list.querySelectorAll('.fb-item')) : []; }

      function recount() {
        const c = { all: 0, new: 0, done: 0, wont: 0 };
        items().forEach(function (it) { c.all++; c[it.dataset.status] = (c[it.dataset.status] || 0) + 1; });
        admin.querySelectorAll('[data-count]').forEach(function (el) {
          el.textContent = c[el.dataset.count] || 0;
        });
      }

      function applyFilter(f) {
        currentFilter = f;
        let visible = 0;
        items().forEach(function (it) {
          const show = f === 'all' || it.dataset.status === f;
          it.hidden = !show;
          if (show) visible++;
        });
        admin.querySelectorAll('[data-fb-filter]').forEach(function (b) {
          b.setAttribute('aria-pressed', b.dataset.fbFilter === f ? 'true' : 'false');
        });
        if (emptyState) emptyState.hidden = visible > 0;
      }

      admin.querySelectorAll('[data-fb-filter]').forEach(function (btn) {
        btn.addEventListener('click', function () { applyFilter(btn.dataset.fbFilter); });
      });

      let toastTimer = null;
      function toast(msg) {
        const existing = document.querySelector('.fb-toast');
        if (existing) existing.remove();
        const t = document.createElement('div');
        t.className = 'fb-toast';
        t.setAttribute('role', 'status');
        t.innerHTML = '<span class="dot"></span>' + msg;
        document.body.appendChild(t);
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { t.remove(); }, 2600);
      }

      function setStatus(item, status) {
        item.dataset.status = status;
        item.classList.toggle('is-done', status === 'done');
        item.classList.toggle('is-wont', status === 'wont');
        const pill = item.querySelector('.fb-status');
        if (pill) {
          pill.className = 'fb-status ' + status;
          pill.innerHTML = '<span class="dot"></span>' + labels[status];
        }
        const actions = item.querySelector('.fb-it-actions');
        if (actions) {
          actions.innerHTML = status === 'new'
            ? '<button class="fb-act wont" data-set="wont">Won\'t do</button>' +
              '<button class="fb-act done" data-set="done">✓ Mark done</button>'
            : '<button class="fb-act reopen" data-set="new">↺ Reopen</button>';
          wireActions(item);
        }
        recount();
        applyFilter(currentFilter);
        toast(status === 'new' ? 'Reopened' : status === 'done' ? 'Marked done' : "Marked won't do");
      }
      function wireActions(item) {
        item.querySelectorAll('[data-set]').forEach(function (b) {
          b.addEventListener('click', function () { setStatus(item, b.dataset.set); });
        });
      }
      items().forEach(wireActions);
      recount();
      applyFilter('all');
    }
  });
})();
