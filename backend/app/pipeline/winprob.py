"""Pure live win-probability model + signal bundle (the deterministic half of the
hybrid; the bounded AI adjustment lives in `live_winprob_agent.py`).

No DB, network, LLM or wall-clock — the match minute is passed in. Three pure
functions, mirroring `standings_math.py`:

- `compute_base`     — calibrated in-play win/draw/loss from score + minutes
                       remaining (time-decayed Poisson/Skellam). The anchor the
                       agent is bounded around.
- `extract_signals`  — a context bundle (live xG/shots/possession, reds, season
                       form, qualification) the Phase-3 agent weighs. Omits any
                       signal whose source is absent — never fabricates a zero.
- `apply_adjustment` — clamps the agent's per-outcome delta to base ±ADJ_BAND
                       and re-normalizes to 100, so the base stays authoritative.
"""
from __future__ import annotations

import math
from typing import Optional

# Tunable constants (referenced by tests).
FULL_TIME_MINUTE = 95      # regulation 90' + ~5' avg stoppage; a lead at 88'-90'
                           # keeps a sliver of uncertainty, elapsed >= 95 collapses.
BASE_GOALS_PER_MATCH = 2.6  # fixed league-average rate; team strength enters ONLY
                           # via the weak prior tilt, never a per-team base rate.
RED_PENALTY = 0.75         # multiplier on the offending side's remaining-goal rate.
PRIOR_WEIGHT = 0.5         # how strongly the pre-match prior tilts the split (weak).
ADJ_BAND = 10              # max points the AI adjustment may move any outcome.
REFRESH_MINUTES = 15       # the agent also refreshes every this-many minutes of play.
_MAX_GOALS = 10            # analytic Poisson sum bound for remaining goals per side.


def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam**k / math.factorial(k)


def _round_to_100(p_home: float, p_draw: float, p_away: float, *, certain: bool) -> dict:
    """Round three probabilities (in [0,1]) to integer percentages summing to 100,
    absorbing the rounding remainder into the largest bucket. While the match is in
    play (`certain` False) no single outcome is allowed to reach a literal 100 — a
    sliver is held back so the bar always reflects that the ball is still rolling."""
    vals = [round(p_home * 100), round(p_draw * 100), round(p_away * 100)]
    remainder = 100 - sum(vals)
    vals[vals.index(max(vals))] += remainder
    if not certain:
        hi = vals.index(max(vals))
        if vals[hi] >= 100:
            vals[hi] = 99
            others = [i for i in range(3) if i != hi]
            j = others[0] if (p_home, p_draw, p_away)[others[0]] >= (p_home, p_draw, p_away)[others[1]] else others[1]
            vals[j] += 1
    return {"home": vals[0], "draw": vals[1], "away": vals[2]}


def _weak_tilt(prior: Optional[dict]) -> float:
    """Home share of the remaining-goal rate (0..1), tilted weakly by the stored
    pre-match forecast. No prior → 0.5 (even). Draw share is ignored."""
    if not prior:
        return 0.5
    home_pct = prior.get("home_pct")
    away_pct = prior.get("away_pct")
    if home_pct is None or away_pct is None or (home_pct + away_pct) == 0:
        return 0.5
    raw = home_pct / (home_pct + away_pct)
    return 0.5 + PRIOR_WEIGHT * (raw - 0.5)


def compute_base(
    home_score: int,
    away_score: int,
    minute: int,
    *,
    prior: Optional[dict] = None,
    home_red: int = 0,
    away_red: int = 0,
) -> dict:
    """Calibrated in-play win/draw/loss split (ints summing to 100). Shifts with
    the score, decays toward the scoreline as the clock runs down, lowers the side
    with a red card, and tilts weakly toward a stored pre-match prior. As the match
    reaches the full-time anchor the split collapses onto the current scoreline."""
    capped = min(max(minute, 0), FULL_TIME_MINUTE)
    frac_remaining = (FULL_TIME_MINUTE - capped) / FULL_TIME_MINUTE
    lambda_total = BASE_GOALS_PER_MATCH * frac_remaining
    w_home = _weak_tilt(prior)
    lambda_home = lambda_total * w_home * (RED_PENALTY**home_red)
    lambda_away = lambda_total * (1 - w_home) * (RED_PENALTY**away_red)

    lead = home_score - away_score
    home_p = _poisson_pmf  # local alias
    p_home = p_draw = p_away = 0.0
    home_pmf = [home_p(g, lambda_home) for g in range(_MAX_GOALS + 1)]
    away_pmf = [home_p(g, lambda_away) for g in range(_MAX_GOALS + 1)]
    for gh in range(_MAX_GOALS + 1):
        for ga in range(_MAX_GOALS + 1):
            prob = home_pmf[gh] * away_pmf[ga]
            diff = lead + (gh - ga)
            if diff > 0:
                p_home += prob
            elif diff == 0:
                p_draw += prob
            else:
                p_away += prob

    total = p_home + p_draw + p_away
    if total <= 0:  # all mass beyond _MAX_GOALS (impossible in practice) — fall back to scoreline
        certain = True
        p_home = 1.0 if lead > 0 else 0.0
        p_draw = 1.0 if lead == 0 else 0.0
        p_away = 1.0 if lead < 0 else 0.0
    else:
        p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total
        certain = frac_remaining <= 0
    return _round_to_100(p_home, p_draw, p_away, certain=certain)


def _possession_number(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        return None


def _stats_by_team(statistics, team) -> dict:
    for entry in statistics or []:
        if (entry.get("team") or {}).get("name") == team:
            return {s.get("type"): s.get("value") for s in (entry.get("statistics") or [])}
    return {}


def _diff(home_stats, away_stats, key) -> Optional[float]:
    hv = _possession_number(home_stats.get(key))
    av = _possession_number(away_stats.get(key))
    if hv is None or av is None:
        return None
    return round(hv - av, 2)


def extract_signals(
    *,
    statistics,
    events,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    home_row=None,
    away_row=None,
) -> dict:
    """Deterministic context bundle for the Phase-3 agent. Keys are present ONLY
    when their source is present — a missing stat/row means a missing key, never a
    fabricated zero. `events` is the normalized MatchEvent list."""
    sig: dict = {}

    home_stats = _stats_by_team(statistics, home_team)
    away_stats = _stats_by_team(statistics, away_team)
    xg = _diff(home_stats, away_stats, "expected_goals")
    if xg is not None:
        sig["xg_diff"] = xg
    shots_on = _diff(home_stats, away_stats, "Shots on Goal")
    if shots_on is not None:
        sig["shots_on_diff"] = int(shots_on)
    possession = _diff(home_stats, away_stats, "Ball Possession")
    if possession is not None:
        sig["possession_diff"] = int(possession)

    home_red = away_red = 0
    for e in events or []:
        if (getattr(e, "type", None) or "").strip().lower() != "card":
            continue
        if "red" not in (getattr(e, "detail", None) or "").strip().lower():
            continue
        side = getattr(e, "side", None)
        if side == "home":
            home_red += 1
        elif side == "away":
            away_red += 1
    if home_red:
        sig["home_red"] = home_red
    if away_red:
        sig["away_red"] = away_red

    def _form(row):
        return {"won": row.won, "drawn": row.drawn, "lost": row.lost} if row else None

    form = {k: v for k, v in (("home", _form(home_row)), ("away", _form(away_row))) if v}
    if form:
        sig["form"] = form
    qualification = {
        k: v
        for k, v in (
            ("home", getattr(home_row, "qualification", None)),
            ("away", getattr(away_row, "qualification", None)),
        )
        if v
    }
    if qualification:
        sig["qualification"] = qualification

    return sig


def live_read_signature(events, status: Optional[str], minute: Optional[int]) -> str:
    """Stable string that changes on a new goal, a new red card, a status
    transition (1H/HT/2H/FT...), OR every `REFRESH_MINUTES` of play. The
    time-bucket term is what makes the agent refresh periodically (so gradual
    xG/possession drift can move the number between goals) using the same
    sig-change gate — no separate timer or column. Yellow cards and minute ticks
    within the same bucket leave it unchanged. Pure; `events` is normalized."""
    n_goals = n_reds = 0
    for e in events or []:
        etype = (getattr(e, "type", None) or "").strip().lower()
        if etype == "goal":
            n_goals += 1
        elif etype == "card" and "red" in (getattr(e, "detail", None) or "").strip().lower():
            n_reds += 1
    bucket = (minute or 0) // REFRESH_MINUTES
    return f"{status}|goals={n_goals}|reds={n_reds}|bucket={bucket}"


def apply_adjustment(base: dict, delta: Optional[dict], *, band: int = ADJ_BAND) -> dict:
    """Fold the agent's per-outcome delta into the base under a hard guarantee: every
    outcome stays within ±`band` of the base AND the three sum to 100. A None/all-zero
    delta returns the base unchanged (a poll with no stored adjustment, or a failed
    agent, degrades cleanly to the calibrated base).

    The effective per-outcome change `e_k = final_k - base_k` is the requested delta
    clamped to `[max(-band, -base_k), band]` (so the final never goes negative and
    never moves more than the band). Because `base` already sums to 100, the result
    sums to 100 iff `sum(e_k) == 0`; the agent only *requests* a zero-sum delta, so any
    surplus is water-filled one point at a time onto the outcomes that still have room
    inside the band. This keeps the calibrated base authoritative — the LLM can sharpen
    context but can never swing the number beyond the band."""
    keys = ("home", "draw", "away")
    if not delta or all(int(delta.get(k) or 0) == 0 for k in keys):
        return dict(base)

    eff = {}
    for k in keys:
        lo = max(-band, -int(base.get(k, 0)))
        eff[k] = max(lo, min(band, int(delta.get(k) or 0)))

    # The effective changes must net to zero to preserve the 100-point total.
    surplus = sum(eff.values())
    guard = 3 * band + 3  # ample bound: total room across 3 outcomes is < 3*band
    while surplus != 0 and guard > 0:
        guard -= 1
        if surplus > 0:  # remove a point from the most-raised outcome that can still drop
            movable = [k for k in keys if eff[k] > max(-band, -int(base.get(k, 0)))]
            if not movable:
                break
            k = max(movable, key=lambda k: eff[k])
            eff[k] -= 1
            surplus -= 1
        else:  # add a point to the most-lowered outcome that can still rise
            movable = [k for k in keys if eff[k] < band]
            if not movable:
                break
            k = min(movable, key=lambda k: eff[k])
            eff[k] += 1
            surplus += 1

    return {k: int(base.get(k, 0)) + eff[k] for k in keys}
