#!/usr/bin/env python3
"""
Verification script for Appendix A of:
  de Miranda, Nagy, Popescu-Bodorin,
  "Privacy Risk Profiling in Claude Code-Based LLM Access Architectures
   -- A Systematic Analysis", IJCCC 2026.

Checks:
  (1) every row of the scoring record reproduces its published score
      to one decimal place under Score = 3*AV + 2*PR + 2*UI + 3*C;
  (2) the five class statistics of Table 6 are reproduced from the record
      (mean, range, n) with the Hybrid class at mode-level granularity n=4;
  (3) the T0 weighted-mean identity 0.6*2.0 + 0.4*5.0 = 3.2 holds.

The script exits with status 0 on success and status 1 on any failure.
"""

import csv
import sys
from pathlib import Path

W = {"AV": 3.0, "PR": 2.0, "UI": 2.0, "C": 3.0}

DATA_FILE = Path(__file__).parent / "015.appendix_a_scoring.csv"

CLASS_STATS_TARGET = {
    "Pure Local":        (0.8, (0.0, 2.0), 4),
    "Hybrid":            (3.2, (2.0, 5.0), 4),
    "Free Cloud":        (7.5, (6.5, 8.5), 10),
    "Paid/Temp":         (6.8, (6.0, 7.5), 4),
    "Commercial":        (7.3, (6.5, 8.3), 3),
}

def load_rows():
    with DATA_FILE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def score_row(row):
    return round(
        W["AV"] * float(row["AV"])
        + W["PR"] * float(row["PR"])
        + W["UI"] * float(row["UI"])
        + W["C"] * float(row["C"]),
        1,
    )

def main():
    rows = load_rows()
    failures = []

    # (1) per-row score reproduction
    for r in rows:
        s = score_row(r)
        target = float(r["score"])
        if s != target:
            failures.append(f"{r['id']}: computed {s}, published {target}")

    # (2) class statistics
    classes = {}
    for r in rows:
        classes.setdefault(r["class"], []).append(float(r["score"]))

    for cls, (mean_t, (min_t, max_t), n_t) in CLASS_STATS_TARGET.items():
        v = classes.get(cls, [])
        if len(v) != n_t:
            failures.append(f"{cls}: n={len(v)}, expected {n_t}")
            continue
        mean_v = round(sum(v) / len(v), 1)
        if mean_v != mean_t:
            failures.append(f"{cls}: mean={mean_v}, expected {mean_t}")
        if min(v) != min_t or max(v) != max_t:
            failures.append(
                f"{cls}: range=[{min(v)}, {max(v)}], "
                f"expected [{min_t}, {max_t}]"
            )

    # (3) T0 weighted-mean identity
    t0 = {r["regime"]: float(r["score"]) for r in rows
          if r["id"].startswith("T0") and r["regime"] in ("light", "heavy")}
    if "light" in t0 and "heavy" in t0:
        ident = round(0.6 * t0["light"] + 0.4 * t0["heavy"], 1)
        if ident != 3.2:
            failures.append(
                f"T0 weighted mean: 0.6*{t0['light']} + 0.4*{t0['heavy']} "
                f"= {ident}, expected 3.2"
            )
    else:
        failures.append("T0 light/heavy rows not found for identity check")

    if failures:
        print("FAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"OK: {len(rows)} rows verified.")
    print("OK: all five class statistics reproduced.")
    print("OK: T0 weighted-mean identity holds.")
    return 0

if __name__ == "__main__":
    sys.exit(main())