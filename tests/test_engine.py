import json
from datetime import date
from pathlib import Path

from trainers.engine import ROOT, Data, today

PLAN = json.loads((ROOT / "plan" / "block2.json").read_text())


def make(runs=(), log=(), state=None):
    state = state or {"week": 2, "done": [0], "pending": []}
    log = [{"date": d, "type": t, "strain": s, "minutes": "", "notes": n} for d, t, s, n in log]
    runs = [{"date": d, "kind": k} for d, k in runs]
    return Data(plan=PLAN, state=state, runs=runs, log=log)


def test_rest_after_run_day():
    b = today(make(runs=[("2026-10-10", "easy")]), date(2026, 10, 11))
    assert b.verdict == "rest"


def test_quality_after_padel_becomes_easy():
    b = today(make(runs=[("2026-10-08", "easy")], log=[("2026-10-10", "padel", "17", "")]), date(2026, 10, 11))
    assert b.session["type"] == "threshold"
    assert b.verdict == "easy-instead"
    assert any("10 bpm hot" in f for f in b.flags)


def test_low_strain_padel_still_blocks_quality_but_no_hot_flag():
    b = today(make(runs=[("2026-10-08", "easy")], log=[("2026-10-10", "padel", "12", "")]), date(2026, 10, 11))
    assert b.verdict == "easy-instead"
    assert not any("hot" in f for f in b.flags)


def test_ache_swaps_quality():
    b = today(make(runs=[("2026-10-08", "easy")], log=[("2026-10-11", "ache", "", "right medial knee")]), date(2026, 10, 11))
    assert b.verdict == "easy-instead"


def test_hard_streak_blocks_quality():
    log = [("2026-10-09", "hiit", "", ""), ("2026-10-10", "tonal", "", "lower body")]
    b = today(make(runs=[("2026-10-07", "easy")], log=log), date(2026, 10, 11))
    assert b.verdict == "easy-instead"


def test_clean_quality_day():
    b = today(make(runs=[("2026-10-08", "easy")]), date(2026, 10, 11))
    assert b.verdict == "run" and b.session["type"] == "threshold"


def test_baseline_waits_for_two_days_off_and_no_padel():
    st = {"week": 1, "done": [0, 1], "pending": [{"type": "baseline", "dist_mi": 2}]}
    assert today(make(runs=[("2026-10-02", "threshold")], state=st), date(2026, 10, 4)).verdict == "rest"
    assert today(make(runs=[("2026-10-02", "threshold")], state=st), date(2026, 10, 5)).verdict == "run"
    padel = [("2026-10-04", "padel", "", "")]
    assert today(make(runs=[("2026-10-02", "threshold")], log=padel, state=st), date(2026, 10, 5)).verdict == "rest"


def test_week_rolls_over():
    st = {"week": 1, "done": [0, 1, 2], "pending": []}
    s = make(state=st).next_session()
    assert s["week"] == 2 and s["type"] == "easy"


def test_real_data_loads():
    Data.load()
