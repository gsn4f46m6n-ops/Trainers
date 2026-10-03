# Trainers

Neil's training hub: running, padel, Tonal, HIIT/leg press. Profile, rules and data caveats: [docs/CONTEXT.md](docs/CONTEXT.md).

## Setup
```bash
git submodule update --init      # pulls vendor/tonal-api (unofficial Tonal toolkit)
```

## Tonal
```bash
python -m trainers.tonal_sync auth <email> <password>   # once; stores tokens in ~/.config/trainers/tonal, never the password
python -m trainers.tonal_sync                           # sync history, per-set details, readiness, strength
```
Needs network access to `api.tonal.com` and `tonal.auth0.com`. Raw pulls land in `data/raw/tonal/` (gitignored).
