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
Needs network access to `api.tonal.com` and `tonal.auth0.com`. Raw pulls land in `data/raw/tonal/` (gitignored).

## Daily brief
```bash
python -m trainers today [YYYY-MM-DD]   # what should today be?
python -m trainers runs                 # run history in mi and min/mi
```
- Plan: `plan/block2.json` (8 weeks). Progress: `plan/state.json` (current week, sessions done, pending tests).
- Runs: `data/runs.json`, normalized from Strava.
- Everything else goes in `data/log.csv`: `padel`, `fastfeet`, `tonal` (put "lower"/"legs" in notes for leg days), `legpress`, `hiit`, `alcohol`, `travel`, `heat`, `ache`.

Rules encoded: rest day between runs; no quality the day after padel; aches swap quality for easy; 3+ hard days in a row blocks quality; baseline needs 2 days off + no padel the day before; HR confounder flags (padel strain >15, alcohol, travel, heat).
