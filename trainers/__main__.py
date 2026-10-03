"""CLI: python -m trainers [today [YYYY-MM-DD] | runs]"""
import sys
from datetime import date

from .engine import M_PER_MI, Data, pace, render, today


def cmd_today(args):
    d = date.fromisoformat(args[0]) if args else date.today()
    data = Data.load()
    print(render(today(data, d), data.plan))


def cmd_runs(args):
    print(f"{'date':10}  {'place':20} {'mi':>5} {'pace':>6} {'hr':>4}  kind       confounders")
    for r in Data.load().runs:
        print(f"{r['date']:10}  {r['place'][:20]:20} {r['dist_m'] / M_PER_MI:5.2f} {pace(r['dist_m'], r['moving_s']):>6} "
              f"{r['avg_hr']:4.0f}  {r['kind']:10} {', '.join(r.get('confounders', []))}")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["today"]
    {"today": cmd_today, "runs": cmd_runs}[cmd](rest)
