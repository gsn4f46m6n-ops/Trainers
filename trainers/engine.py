"""Daily decision engine: "what should today be?"

Inputs are plain files so anything (Claude, a script, Neil by hand) can update them:
  plan/block2.json  the 8-week plan
  plan/state.json   where Neil is in it
  data/runs.json    runs (normalized from Strava)
  data/log.csv      everything else: padel, fastfeet, tonal, legpress, hiit, alcohol, travel, heat, ache
"""
import csv
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M_PER_MI = 1609.344

PADEL_HOT_STRAIN = 15        # above this, next-day run HR reads 10+ bpm hot
HARD_RUN_KINDS = {"sprint", "threshold", "test", "effort", "time_trial"}
HARD_LOG_TYPES = {"hiit", "legpress"}
QUALITY_TYPES = {"sprint", "threshold", "time_trial"}


def pace(dist_m, secs):
    """min/mi string from metres and seconds."""
    s = secs / (dist_m / M_PER_MI)
    return f"{int(s // 60)}:{int(round(s % 60)):02d}"


@dataclass
class Data:
    plan: dict
    state: dict
    runs: list
    log: list

    @classmethod
    def load(cls, root=ROOT):
        root = Path(root)
        with open(root / "data" / "log.csv") as f:
            log = [r for r in csv.DictReader(f)]
        return cls(
            plan=json.loads((root / "plan" / "block2.json").read_text()),
            state=json.loads((root / "plan" / "state.json").read_text()),
            runs=json.loads((root / "data" / "runs.json").read_text()),
            log=log,
        )

    def runs_on(self, d):
        return [r for r in self.runs if r["date"] == d.isoformat()]

    def log_on(self, d, *types):
        return [e for e in self.log if e["date"] == d.isoformat() and (not types or e["type"] in types)]

    def last_run_date(self, before):
        ds = [date.fromisoformat(r["date"]) for r in self.runs if r["date"] < before.isoformat()]
        return max(ds) if ds else None

    def is_hard_day(self, d):
        if any(r["kind"] in HARD_RUN_KINDS for r in self.runs_on(d)):
            return True
        for e in self.log_on(d, "padel"):
            # Unknown strain counts as hard: Neil's padel usually lands at 16-20.
            if not e["strain"] or float(e["strain"]) >= PADEL_HOT_STRAIN:
                return True
        if self.log_on(d, *HARD_LOG_TYPES):
            return True
        return any("leg" in e["notes"].lower() or "lower" in e["notes"].lower() for e in self.log_on(d, "tonal"))

    def next_session(self):
        if self.state.get("pending"):
            return self.state["pending"][0]
        week = self.state["week"]
        if week > len(self.plan["weeks"]):
            return None
        remaining = [i for i in range(3) if i not in self.state.get("done", [])]
        if not remaining:
            week += 1
            if week > len(self.plan["weeks"]):
                return None
            remaining = [0]
        return {**self.plan["weeks"][week - 1][remaining[0]], "week": week}


@dataclass
class Brief:
    day: date
    verdict: str                     # "run", "rest", "easy-instead"
    session: dict | None
    reasons: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    reminders: list = field(default_factory=list)


def describe(s):
    t = s["type"]
    if t == "easy":
        return f"Easy {s['min']} min"
    if t == "sprint":
        return f"Sprints {s['reps']}x{s['secs']}s" + (f" ({s['recovery_s']}s recovery)" if "recovery_s" in s else "")
    if t == "threshold":
        return f"Threshold {s['reps']}x{s['mins']} min" + (f" ({s['recovery_s']}s recovery)" if "recovery_s" in s else "")
    if t == "time_trial":
        return "Mile time trial (track)"
    if t == "baseline":
        return f"Baseline test: {s['dist_mi']} mi flat, easy effort"
    return t


def today(data: Data, day: date) -> Brief:
    yday = day - timedelta(days=1)
    session = data.next_session()
    b = Brief(day=day, verdict="run", session=session)
    if session is None:
        b.verdict = "rest"
        b.reasons.append("Block 2 is complete. Time to plan Block 3.")
        return b

    # Rest day between runs.
    last = data.last_run_date(day)
    if last == yday:
        b.verdict = "rest"
        b.reasons.append(f"Ran yesterday ({last}). At least one rest day between runs.")

    padel_yday = data.log_on(yday, "padel")
    hot_padel = any(not e["strain"] or float(e["strain"]) > PADEL_HOT_STRAIN for e in padel_yday)

    # Baseline has its own preconditions.
    if session["type"] == "baseline" and b.verdict == "run":
        days_off = (day - last).days - 1 if last else 99
        if days_off < 2:
            b.verdict = "rest"
            b.reasons.append(f"Baseline needs 2 days off running; you've had {days_off}. Earliest: {last + timedelta(days=3)}.")
        elif padel_yday:
            b.verdict = "rest"
            b.reasons.append("Baseline needs no padel the day before. Do it the next clean day.")

    # Quality rules.
    if session["type"] in QUALITY_TYPES and b.verdict == "run":
        aches = [e for d in (day, yday) for e in data.log_on(d, "ache")]
        if padel_yday:
            b.verdict = "easy-instead"
            b.reasons.append("Padel yesterday: no quality session today. Run easy or move quality to tomorrow.")
        elif aches:
            b.verdict = "easy-instead"
            b.reasons.append(f"Ache logged ({aches[0]['notes'] or 'see log'}): swap quality for easy, or walk.")

    # Load stack: 3+ hard days in a row including today's plan.
    streak = 0
    d = yday
    while data.is_hard_day(d):
        streak += 1
        d -= timedelta(days=1)
    if streak >= 2 and session["type"] in QUALITY_TYPES and b.verdict == "run":
        b.verdict = "easy-instead"
        b.reasons.append(f"{streak} hard days in a row already; a quality run would make {streak + 1}.")
    elif streak >= 3:
        b.flags.append(f"{streak} hard days in a row. Keep today genuinely easy.")

    # HR confounders.
    if hot_padel:
        b.flags.append("Padel strain >15 yesterday: expect HR ~10 bpm hot. Judge by talk test, not pace.")
    for kind, msg in (("alcohol", "Alcohol yesterday: HR reads ~10 bpm high."),
                      ("travel", "Travel: HR reads high; don't compare to home benchmarks."),
                      ("heat", "Heat: HR reads high; slow down to hold the HR cap.")):
        if data.log_on(yday, kind) or data.log_on(day, kind):
            b.flags.append(msg)

    if b.verdict != "rest":
        b.reminders += [
            "Glute activation first: bridges 2x15, right single-leg bridges 2x12, banded walks, clamshells.",
            "Short, quick steps; foot under the hips.",
        ]
    return b


def render(b: Brief, plan: dict) -> str:
    lines = [f"# {b.day:%a %b %-d}"]
    s = b.session
    if b.verdict == "rest":
        lines.append("**Rest from running.**" + (f" Next up: {describe(s)}." if s else ""))
    elif b.verdict == "easy-instead":
        lines.append(f"**Easy run instead of {describe(s)}.** Keep it 25-30 min at HR 135-148.")
    else:
        t = plan["session_types"][s["type"]]
        lines.append(f"**{describe(s)}**" + (f" (week {s['week']})" if "week" in s else ""))
        lines.append(f"- Target: {t['pace']}" + (f", HR {t['hr'][0]}-{t['hr'][1]}" if "hr" in t else ""))
        if "recovery" in t:
            lines.append(f"- Recovery: {t['recovery']}")
        lines.append(f"- Warmup: {t['warmup']}. Cooldown: {t['cooldown']}.")
        lines.append(f"- {t['cue']}")
    for r in b.reasons:
        lines.append(f"- Why: {r}")
    for f in b.flags:
        lines.append(f"- ⚠ {f}")
    for r in b.reminders:
        lines.append(f"- {r}")
    return "\n".join(lines)
