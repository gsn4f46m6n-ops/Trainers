# Training context: Neil

Source of truth for the athlete profile, rules, and data caveats. Handed over from earlier agent sessions (Oct 3, 2026).

## Who and why
- Strength-trained for years, plays padel 2-3x/week (strain 16-20 sessions), plus coach-designed "fast feet" drills (12 min, 45s on / 15s off) up to 5x/week.
- Started running Aug 3, 2026 from a low aerobic base. Goal is NOT race times. Goal is on-court endurance: recover between points, stay explosive late in matches, stay low in the athletic stance.
- Body composition: on an oral GLP-1 (orforglipron), ~187 -> ~177-178 lb over ~3 months. Target 175, then 2-4 weeks maintenance, then a lean build (~+200-300 kcal). Protein target 140-170 g/day. Appetite suppression means eating on a schedule, not on hunger.
- Known weaknesses: right glute under-recruits, left calf endurance, poor deceleration ("strong engine, weak brakes"), staying low in stance.
- Recurring issues: right medial knee (pes anserine) ache, kneecap ache after fast running, calves after long efforts, tailbone-area back ache when fatigued.

## History so far
- 8-week run/walk program -> continuous running, 28 runs by Sep 26. Zone 2 and fitness improved clearly.
- First 5K (Sep 12, 2026): 34:43, 3.12 mi, splits 11:16/10:52/11:13/11:46, HR 146 -> 180, avg 163. Went out too fast in mile 2.
- Current block (3 runs/wk): 2 easy + 1 quality, alternating 4-5x3 min hard and 8-12x15 s sprints. Sprint pace is 6:00-7:00/mi.
- Benchmarks:
  - Sep 14, home route, easy: 12:48/mi, Whoop avg HR 137
  - Sep 18, same route, easy after hard week: 12:44/mi, avg HR 149 (fatigue)
  - Sep 22, Mallorca (flat road): mile 1 11:43 @ HR 140; mile 2 10:29 @ HR 167 (chased other runners)
  - Sep 30, home: fastest mile ever, 9:31, avg HR 160
  - Oct 2, Maryland, heat + hills, day after 1 hr padel in heat: 4x3 min became hill efforts, avg HR 163, max 194, one walk break
- Measured max HR: 201 (padel). Whoop zones recalibrated Aug 13, Aug 27, Sep 11, Sep 25, so zone-time across dates is not directly comparable.

## Rules of thumb (encode as alerts / defaults)
- Easy runs ~12:45/mi at HR 137-148 on home terrain. Perceived exertion lags: "felt easy" has repeatedly coincided with higher HR.
- Padel strain > ~15 -> next-day run reads 10+ bpm hot. No quality running the day after padel.
- Alcohol raises next-day HR ~10 bpm. Travel and heat raise it too. Annotate runs with these confounders.
- Best data comes from two-day gaps between runs. Tendon/bone adapt slower than the heart: watch step-count jumps (impact volume) separately from HR.
- Pre-padel meal timing (GLP-1): real meal 3+ h before a match, only light fast carbs inside 1 h. See [PADEL.md](PADEL.md).
- Cutting phase: don't add cardio to speed up the cut. Protect lean mass with protein and lifting.

## Data sources and caveats
- **Strava**: official API (MCP connector works). Runs only from Sep 12 onward. Strava HR zones use age-based max 188, not 201, so zone labels run hot. Barometric elevation is reliable. Gives GAP, splits, best efforts, predicted 5K (~30:40-31:45). Returns metric units.
- **Whoop**: developer API (OAuth). Strain, recovery, HRV, RHR, sleep, zone time, steps per activity. Elevation is GPS-estimated and inflated (316 ft vs Strava 70 ft, same route). Wrist HR unreliable in padel. Padel calories inflated (~1,000+ kcal/hr).
- **Tonal**: no official API. Unofficial integration must be optional; app must work without it (manual/CSV fallback). Needed: workout volume, eccentric-mode use, movement-level progress, weekly lower-body load.
- **Withings**: body composition (weight trend, lean mass estimate). Integration not yet scoped.
- Display in miles and min/mi.

## Derived metrics
1. Pace at fixed HR on a fixed route (cleanest fitness signal; compare monthly).
2. Minutes above HR threshold per minute of running (only across similar session structures).
3. HR recovery depth between reps (bpm drop over a 90-120 s walk).
4. Cardiac drift (first-half vs second-half HR at the same pace).
5. Ground contacts: steps and distance per step (cadence proxy and impact load).
6. Weekly load stack: padel + run + lifting strain, flag 3+ hard days in a row.
7. Padel session shape: share of time in Z4/5, valley depth between points (trend only).

## Questions the app answers
- Am I fitter? (1, 3, 4 over time, annotated with terrain, heat, alcohol, prior-day padel)
- What should today be? (rules + Whoop recovery + yesterday's strain)
- Is lean mass holding during the cut? (protein + Tonal volume + weight trend; DEXA is the real check)
- Is knee/calf risk rising? (step jumps, consecutive hard days, speed spikes)

## Open questions
- Does Whoop's API expose per-activity HR streams or only summaries?
- Tonal data access (see findings below).
- Backfill pre-Sep-12 history from Whoop?

---

## Findings (Oct 3, 2026)

### Strava (pulled via connector)
8 runs since Sep 12. No padel or Tonal sessions are in Strava; older entries are Peloton rides (2024 to Jun 2026).

| Date | Place | Dist | Pace | Elev (Strava) | Note |
|---|---|---|---|---|---|
| Oct 2 | Montgomery Co., MD | 2.46 mi | 13:13 | 147 ft | Heat/hills, post-padel; hill efforts |
| Sep 30 | Moss Beach (home) | 1.01 mi | 9:31 | 51 ft | Fastest mile |
| Sep 26 | San Sebastián | 2.51 mi | 11:26 | 34 ft | Not in handover notes |
| Sep 22 | Muro, Mallorca | 2.30 mi | 10:54 | 0 ft | Chased runners in mile 2 |
| Sep 18 | Moss Beach | 2.00 mi | 12:44 | 70 ft | Easy, HR 149 (fatigue) |
| Sep 16 | Moss Beach | 1.47 mi | 11:23 | 18 ft | Sprint session (max 5.3 m/s = 5:04/mi) |
| Sep 14 | Moss Beach | 2.02 mi | 12:46 | 70 ft | Easy, HR 137 baseline |
| Sep 12 | Moss Beach | 3.10 mi | 11:08 | 91 ft | First 5K (Whoop said 450 ft) |

Strava's training-plan endpoint only offers Runna; the running plan lives outside Strava.

### Tonal
[ericlitman/tonal-api](https://github.com/ericlitman/tonal-api) (MIT, Python 3.10+): unofficial, reverse-engineered, Auth0 email/password login that stores tokens. CLI plus MCP server.
- Read: workout history with per-set weight/reps, est. 1RM, peak power, range of motion, rep consistency, L/R side, muscle readiness 0-100, strength scores, volume report.
- Write: can build and push custom workouts (eccentric, chains, spotter, drop sets).
- Covers the needed data (volume, eccentric use, movement progress, lower-body load). Still unofficial and could break, so keep the CSV/manual fallback.
- Alternatives: BrianVia/tonal-mcp-cloudflare-workers, Emre-C/toneget (JSON export).
