import json
from datetime import date

from trainers.tonal_report import summarize


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_summarize_regions_eccentric_and_weeks(tmp_path):
    _write(tmp_path / "movements.json", [
        {"id": "sq", "name": "Goblet Squat", "bodyRegion": "LowerBody"},
        {"id": "row", "name": "Seated Row", "bodyRegion": "UpperBody"},
    ])
    _write(tmp_path / "activities.json", [
        {"activityId": "a1", "activityType": "Internal", "activityTime": "2026-09-08T17:00:00Z",
         "workoutPreview": {"workoutTitle": "Legs", "targetArea": "LOWER BODY", "totalVolume": 1500, "totalDuration": 1800}},
        {"activityId": "x1", "activityType": "External", "activityTime": "2026-09-09T17:00:00Z",
         "workoutPreview": {"totalVolume": 0, "totalDuration": 1200}},
    ])
    _write(tmp_path / "workouts" / "a1.json", {"id": "a1", "workoutSetActivity": [
        {"movementId": "sq", "repCount": 6, "volume": 1000, "eccentric": True, "oneRepMax": 90.4},
        {"movementId": "row", "repCount": 8, "volume": 500, "eccentric": False, "warmUp": True},
        {"movementId": "row", "repCount": 0, "volume": 0},
    ]})
    s = summarize(tmp_path, until=date(2026, 9, 21))
    assert s["totals"]["sessions"] == 1                      # External (Whoop import) skipped
    assert s["totals"]["lower"] == 1000 and s["totals"]["upper"] == 500
    assert s["totals"]["ecc_sets"] == 1 and s["totals"]["lower_ecc_sets"] == 1
    assert [w["week"] for w in s["weeks"]] == ["2026-09-07", "2026-09-14", "2026-09-21"]  # empty weeks filled
    squat = next(m for m in s["movements"] if m["name"] == "Goblet Squat")
    assert squat["est_1rm"] == [{"date": "2026-09-08", "lb": 90}]
    row = next(m for m in s["movements"] if m["name"] == "Seated Row")
    assert row["est_1rm"] == []                              # warm-up sets don't count toward 1RM
