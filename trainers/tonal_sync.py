"""Pull Tonal data into data/raw/tonal/ via the unofficial tonal-api toolkit.

Tokens live outside the repo (TONAL_TOKEN_DIR, default ~/.config/trainers/tonal).
First-time login:
    python -m trainers.tonal_sync auth      # reads TONAL_EMAIL / TONAL_PASSWORD
    # or passwordless: auth-start <email>, then auth-verify <code>
Then:
    python -m trainers.tonal_sync            # sync history, details, readiness, strength
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Local .env (gitignored) fills in anything not already set in the environment.
if (ROOT / ".env").exists():
    for line in (ROOT / ".env").read_text().splitlines():
        key, sep, val = line.partition("=")
        if sep and not key.strip().startswith("#") and val.strip():
            os.environ.setdefault(key.strip(), val.strip())
os.environ.setdefault("TONAL_TOKEN_DIR", str(Path.home() / ".config" / "trainers" / "tonal"))
Path(os.environ["TONAL_TOKEN_DIR"]).mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "vendor" / "tonal-api"))

import tonal_tool as tt  # noqa: E402

OUT = ROOT / "data" / "raw" / "tonal"


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _check(data, what):
    if isinstance(data, dict) and "error" in data:
        sys.exit(f"Tonal {what}: {data['error']}")
    return data


def sync(limit=100):
    uid = tt.get_user_id()
    if not uid:
        sys.exit("Not authenticated. Run: python -m trainers.tonal_sync auth <email> <password>")

    acts = _check(tt.api_get(f"/v6/users/{uid}/activities", params={"limit": limit}), "history")
    if isinstance(acts, dict):
        acts = acts.get("activities", acts.get("data", []))
    _write(OUT / "activities.json", acts)

    # Per-workout detail is immutable once done, so only fetch what we don't have.
    new = 0
    for act in acts:
        aid = act.get("activityId")
        path = OUT / "workouts" / f"{aid}.json"
        if not aid or path.exists():
            continue
        _write(path, _check(tt.api_get(f"/v6/users/{uid}/workout-activities/{aid}"), f"workout {aid}"))
        new += 1

    _write(OUT / "readiness.json", _check(tt.api_get(f"/v6/users/{uid}/muscle-readiness/current"), "readiness"))
    _write(OUT / "strength_history.json",
           _check(tt.api_get(f"/v6/users/{uid}/strength-scores/history", params={"limit": 100}), "strength"))
    print(f"Tonal: {len(acts)} activities, {new} new workout details -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ("auth", "auth-start", "auth-verify", "status", "check-health"):
        if args == ["auth"]:
            # Credentials from the environment, so they never appear in a shell command or chat.
            args = ["auth", os.environ.get("TONAL_EMAIL", ""), os.environ.get("TONAL_PASSWORD", "")]
        handler = {"auth": tt.cmd_auth, "auth-start": tt.cmd_auth_start, "auth-verify": tt.cmd_auth_verify,
                   "status": tt.cmd_status, "check-health": tt.cmd_check_health}[args[0]]
        print(json.dumps(handler(args[1:]), indent=2))
    else:
        sync()
