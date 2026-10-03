# Trainers

Neil's training hub: running, padel, Tonal, HIIT/leg press. Profile, rules and data caveats: [docs/CONTEXT.md](docs/CONTEXT.md).

## Setup
```bash
git submodule update --init      # pulls vendor/tonal-api (unofficial Tonal toolkit)
```

## Tonal
```bash
python -m trainers.tonal_sync auth                      # once; reads TONAL_EMAIL / TONAL_PASSWORD env vars, stores tokens in ~/.config/trainers/tonal
python -m trainers.tonal_sync                           # sync history, per-set details, readiness, strength
```
```bash
python -m trainers.tonal_report                         # weekly volume, lower-body load, eccentric use, top movements -> data/raw/tonal/summary.json
```
Needs network access to `api.tonal.com` and `tonal.auth0.com`. Raw pulls land in `data/raw/tonal/` (gitignored).

## Training Hub (phone app)
`app/hub.html`, published as a private claude.ai artifact: https://claude.ai/artifact/B3kriev9zjHduWMxRXe97L
- **Run**: interval timer built from `plan/block2.json` (voice + beeps, keeps the screen on), custom intervals, "mark session done".
- **Fast feet**: 12 drills × 45 s on / 15 s off, logged when finished.
- **Tonal**: weekly load chart, top movements with est. 1RM, and three planned routines (Brakes, Engine, Spring) with placement rules.
- **Review**: pick a Strava run (live via the Strava connector) or a Tonal workout, add Whoop numbers by hand, get splits / drift / rep HR recovery and a Claude analysis; save it.
- **Padel**: paste a match-review transcript; Claude scores the bandeja focus, failure modes, weaknesses (uniform-attention rule), mental and physical markers; trend chart.
- **Summary**: 14-day hard-day stack, weekly miles, and a written summary across everything.

Logs live in the artifact's database (`sessions`, `matches`, `state/run`, `tonal/summary`). The page can't reach Tonal or Whoop itself: refresh Tonal by running `tonal_sync` + `tonal_report` here and writing `summary.json` to `tonal/summary`.

## Daily brief
```bash
python -m trainers today [YYYY-MM-DD]   # what should today be?
python -m trainers runs                 # run history in mi and min/mi
```
- Plan: `plan/block2.json` (8 weeks). Progress: `plan/state.json` (current week, sessions done, pending tests).
- Runs: `data/runs.json`, normalized from Strava.
- Everything else goes in `data/log.csv`: `padel`, `fastfeet`, `tonal` (put "lower"/"legs" in notes for leg days), `legpress`, `hiit`, `alcohol`, `travel`, `heat`, `ache`.

Rules encoded: rest day between runs; no quality the day after padel; aches swap quality for easy; 3+ hard days in a row blocks quality; baseline needs 2 days off + no padel the day before; HR confounder flags (padel strain >15, alcohol, travel, heat).
