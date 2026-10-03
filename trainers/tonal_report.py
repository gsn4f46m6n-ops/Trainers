"""Summarize synced Tonal data (data/raw/tonal/) into data/raw/tonal/summary.json.

    python -m trainers.tonal_report          # writes summary.json, prints a short digest

Weeks start Monday (Pacific time). Volume is Tonal's own figure in lb (weight x reps, warm-ups included).
Body region comes from the movement catalog (movements.json, pulled by tonal_sync).
"""
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "tonal"
PT = ZoneInfo("America/Los_Angeles")
REGIONS = {"LowerBody": "lower", "UpperBody": "upper", "Core": "core"}


def local_day(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(PT).date()


def week_of(d):
    return d - timedelta(days=d.weekday())


def summarize(raw=RAW, until=None):
    acts = json.loads((raw / "activities.json").read_text())
    movements = {m["id"]: m for m in json.loads((raw / "movements.json").read_text())}
    details = {}
    for f in (raw / "workouts").glob("*.json"):
        d = json.loads(f.read_text())
        details[d["id"]] = d

    workouts, weeks = [], defaultdict(lambda: {"sessions": 0, "volume": 0, "minutes": 0, "lower": 0, "upper": 0,
                                               "core": 0, "sets": 0, "ecc_sets": 0, "lower_ecc_sets": 0})
    moves = defaultdict(lambda: {"sets": 0, "volume": 0, "ecc_sets": 0, "days": set(), "best_1rm": {}})
    for a in acts:
        if a.get("activityType") != "Internal":
            continue
        p = a["workoutPreview"]
        day = local_day(a["activityTime"])
        wk = weeks[week_of(day)]
        wk["sessions"] += 1
        wk["volume"] += p.get("totalVolume") or 0
        wk["minutes"] += (p.get("totalDuration") or 0) / 60
        w = {"date": day.isoformat(), "title": p.get("workoutTitle") or "Free Lift", "target": p.get("targetArea") or "",
             "volume": p.get("totalVolume") or 0, "minutes": round((p.get("totalDuration") or 0) / 60),
             "lower": 0, "upper": 0, "core": 0, "sets": 0, "ecc_sets": 0, "top": []}
        per_move = defaultdict(float)
        for s in details.get(a["activityId"], {}).get("workoutSetActivity", []):
            if not s.get("repCount"):
                continue
            m = movements.get(s["movementId"], {})
            name, region = m.get("name", "Unknown"), REGIONS.get(m.get("bodyRegion"), "other")
            vol = s.get("volume") or 0
            ecc = bool(s.get("eccentric"))
            w["sets"] += 1
            w["ecc_sets"] += ecc
            wk["sets"] += 1
            wk["ecc_sets"] += ecc
            if region in ("lower", "upper", "core"):
                w[region] += vol
                wk[region] += vol
            if region == "lower" and ecc:
                wk["lower_ecc_sets"] += 1
            per_move[name] += vol
            mv = moves[name]
            mv["region"] = region
            mv["sets"] += 1
            mv["volume"] += vol
            mv["ecc_sets"] += ecc
            mv["days"].add(day)
            if not s.get("warmUp") and s.get("oneRepMax"):
                k = day.isoformat()
                mv["best_1rm"][k] = max(mv["best_1rm"].get(k, 0), round(s["oneRepMax"]))
        w["top"] = [n for n, _ in sorted(per_move.items(), key=lambda kv: -kv[1])[:4]]
        for k in ("lower", "upper", "core"):
            w[k] = round(w[k])
        workouts.append(w)

    workouts.sort(key=lambda w: w["date"], reverse=True)
    first = min(weeks) if weeks else None
    last = week_of(until or date.today())
    week_rows = []
    d = first
    while d and d <= last:
        row = {k: round(v) for k, v in weeks.get(d, {}).items()} if d in weeks else \
            {"sessions": 0, "volume": 0, "minutes": 0, "lower": 0, "upper": 0, "core": 0, "sets": 0, "ecc_sets": 0,
             "lower_ecc_sets": 0}
        week_rows.append({"week": d.isoformat(), **row})
        d += timedelta(days=7)

    move_rows = []
    for name, mv in moves.items():
        trend = sorted(mv["best_1rm"].items())
        move_rows.append({"name": name, "region": mv["region"], "sessions": len(mv["days"]), "sets": mv["sets"],
                          "volume": round(mv["volume"]), "ecc_sets": mv["ecc_sets"],
                          "last": max(mv["days"]).isoformat(), "est_1rm": [{"date": k, "lb": v} for k, v in trend]})
    move_rows.sort(key=lambda m: (-m["sessions"], -m["sets"]))

    total = sum(w["volume"] for w in workouts)
    sets = sum(w["sets"] for w in workouts)
    ecc = sum(w["ecc_sets"] for w in workouts)
    strength = []
    if (raw / "strength_history.json").exists():
        strength = sorted(({"date": s["activityTime"][:10], "overall": s["overall"], "upper": s["upper"],
                            "lower": s["lower"], "core": s["core"]}
                           for s in json.loads((raw / "strength_history.json").read_text())), key=lambda s: s["date"])
    readiness = json.loads((raw / "readiness.json").read_text()) if (raw / "readiness.json").exists() else {}
    return {
        "generated": datetime.now(PT).isoformat(timespec="minutes"),
        "range": {"first": workouts[-1]["date"] if workouts else None, "last": workouts[0]["date"] if workouts else None},
        "totals": {"sessions": len(workouts), "volume": total, "sets": sets, "ecc_sets": ecc,
                   "lower": sum(w["lower"] for w in workouts), "upper": sum(w["upper"] for w in workouts),
                   "core": sum(w["core"] for w in workouts),
                   "lower_ecc_sets": sum(r["lower_ecc_sets"] for r in week_rows)},
        "weeks": week_rows,
        "workouts": workouts,
        "movements": move_rows[:25],
        "strength": strength,
        "readiness": readiness,
    }


if __name__ == "__main__":
    s = summarize()
    (RAW / "summary.json").write_text(json.dumps(s, indent=1))
    t = s["totals"]
    print(f"Tonal {s['range']['first']}..{s['range']['last']}: {t['sessions']} workouts, {t['volume']:,} lb, "
          f"lower {t['lower'] / max(t['volume'], 1):.0%}, eccentric {t['ecc_sets']}/{t['sets']} sets "
          f"-> {(RAW / 'summary.json').relative_to(RAW.parent.parent.parent)}")
