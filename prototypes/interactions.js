/*
  CJX entrance animations + light interactivity
  Source: ck_docs/UI_SPEC.md §1 CJX, §3 Standings (view toggle)
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
  nz: '<rect width="30" height="20" fill="#00247D"/><path d="M0 0 L12 10 M12 0 L0 10" stroke="#fff" stroke-width="2"/><path d="M0 0 L12 10 M12 0 L0 10" stroke="#C8102E" stroke-width="0.8"/><path d="M6 0 V10 M0 5 H12" stroke="#fff" stroke-width="2.6"/><path d="M6 0 V10 M0 5 H12" stroke="#C8102E" stroke-width="1.3"/><circle cx="23" cy="6" r="1.1" fill="#CC142B" stroke="#fff" stroke-width="0.4"/><circle cx="26.5" cy="10" r="1.1" fill="#CC142B" stroke="#fff" stroke-width="0.4"/><circle cx="22.5" cy="14" r="1.1" fill="#CC142B" stroke="#fff" stroke-width="0.4"/><circle cx="25" cy="16.5" r="0.9" fill="#CC142B" stroke="#fff" stroke-width="0.4"/>'
};

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.flag[data-flag]').forEach(function (el) {
    const code = el.dataset.flag;
    const label = el.dataset.code || code.toUpperCase();
    if (FLAGS[code]) {
      el.innerHTML = '<svg viewBox="0 0 30 20" class="flag-svg" role="img" aria-label="' + label + ' flag">' + FLAGS[code] + '</svg>';
    } else {
      // crest fallback for any team without a built flag
      el.outerHTML = '<span class="crest" style="background:' + (el.dataset.color || '#1e3157') + '">' + label + '</span>';
    }
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
