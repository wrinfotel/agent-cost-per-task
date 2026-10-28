#!/usr/bin/env python3
"""Cost per successful task for coding agents.

Reads a CSV log of agent attempts and reports the numbers that actually matter:
cost per attempt vs cost per *successful* task, the retry tax, and the cache share.

Input CSV columns (header required):
    task_id,outcome,attempt_no,input_tokens,cached_tokens,output_tokens,tool_calls,duration_min,cost_usd

  task_id        your own label for the task; one task may have several attempts
  outcome        success | fail   (success = your pre-registered criterion was met)
  attempt_no     1, 2, 3 ... within that task
  input_tokens   total input tokens of that attempt
  cached_tokens  how many of the input tokens were cache hits
  output_tokens  generated tokens
  tool_calls     number of tool/function calls in the attempt
  duration_min   wall-clock minutes of the attempt
  cost_usd       measured or computed cost of the attempt (empty = unknown)

Usage:
    python3 parse.py sample.csv
    python3 parse.py mylog.csv --out report.csv
    python3 parse.py mylog.csv --review-rate 25   # requires review_minutes per row

Stdlib only. No numbers are invented: everything printed is derived from the CSV.
"""

import argparse
import csv
import sys
from collections import OrderedDict

FIELDS = [
    "task_id", "outcome", "attempt_no", "input_tokens", "cached_tokens",
    "output_tokens", "tool_calls", "duration_min", "cost_usd",
]

# Accepted spellings, so the two log schemas people actually use both work:
#   outcome        -> outcome | attempt_outcome
#   cached_tokens  -> cached_tokens | cached_input_tokens
#   cost_usd       -> cost_usd | measured_cost_usd
ALIASES = {
    "outcome": ("outcome", "attempt_outcome"),
    "cached_tokens": ("cached_tokens", "cached_input_tokens"),
    "cost_usd": ("cost_usd", "measured_cost_usd"),
}
# Recognised but unused: task_final_outcome, tool_cost_usd, model, date, notes


def resolve_columns(fieldnames):
    """Map canonical field -> actual column name; report what is missing."""
    columns = {}
    missing = []
    for field in FIELDS:
        for name in ALIASES.get(field, (field,)):
            if name in fieldnames:
                columns[field] = name
                break
        else:
            missing.append(field)
    return columns, missing



def num(value):
    """Parse a number, treating empty/unknown as None."""
    if value is None:
        return None
    value = str(value).strip()
    if value == "" or value.lower() in {"na", "n/a", "unknown", "-"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load(path, review_rate=None):
    tasks = OrderedDict()
    unknown_cost_rows = 0
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns, missing = resolve_columns(reader.fieldnames or [])
        if missing:
            sys.exit(f"CSV is missing column(s): {', '.join(missing)}")
        if review_rate is not None and "review_minutes" not in (reader.fieldnames or []):
            sys.exit("--review-rate requires a review_minutes column with measured human review time for every attempt")
        for row in reader:
            task_id = (row.get(columns["task_id"]) or "").strip()
            if not task_id:
                continue
            cost = num(row.get(columns["cost_usd"]))
            review_minutes = num(row.get("review_minutes"))
            if review_rate is not None and (review_minutes is None or review_minutes < 0):
                sys.exit(f"Invalid or missing review_minutes for task {task_id}; use 0 for no review")
            if cost is None:
                unknown_cost_rows += 1
            attempt = {
                "outcome": (row.get(columns["outcome"]) or "").strip().lower(),
                "input_tokens": num(row.get(columns["input_tokens"])) or 0.0,
                "cached_tokens": num(row.get(columns["cached_tokens"])) or 0.0,
                "output_tokens": num(row.get(columns["output_tokens"])) or 0.0,
                "tool_calls": num(row.get(columns["tool_calls"])) or 0.0,
                "duration_min": num(row.get(columns["duration_min"])) or 0.0,
                "cost_usd": cost,
                "review_minutes": review_minutes,
            }
            tasks.setdefault(task_id, []).append(attempt)
    return tasks, unknown_cost_rows


def summarize(tasks, review_rate=None):
    total_attempts = 0
    total_cost = 0.0
    fail_cost = 0.0        # attempts belonging to tasks that never succeeded
    fail_cost_all = 0.0    # every attempt that did not itself succeed
    input_tokens = 0.0
    cached_tokens = 0.0
    output_tokens = 0.0
    duration = 0.0
    review_duration = 0.0
    successful = 0
    attempts_on_success = 0

    for task_id, attempts in tasks.items():
        total_attempts += len(attempts)
        solved = any(a["outcome"] == "success" for a in attempts)
        if solved:
            successful += 1
            attempts_on_success += len(attempts)
        for a in attempts:
            total_cost += a["cost_usd"] if a["cost_usd"] is not None else 0.0
            review_duration += a["review_minutes"] if a["review_minutes"] is not None else 0.0
            input_tokens += a["input_tokens"]
            cached_tokens += a["cached_tokens"]
            output_tokens += a["output_tokens"]
            duration += a["duration_min"]
            if a["outcome"] != "success":
                fail_cost_all += a["cost_usd"] if a["cost_usd"] is not None else 0.0
                if not solved:
                    fail_cost += a["cost_usd"] if a["cost_usd"] is not None else 0.0

    review_cost = (review_duration / 60.0) * review_rate if review_rate is not None else 0.0
    grand_total = total_cost + review_cost

    return {
        "tasks": len(tasks),
        "successful": successful,
        "total_attempts": total_attempts,
        "total_cost": total_cost,
        "review_cost": review_cost,
        "grand_total": grand_total,
        "cost_per_attempt": (grand_total / total_attempts) if total_attempts else None,
        "cost_per_success": (grand_total / successful) if successful else None,
        "fail_cost_all": fail_cost_all,
        "failed_attempts_share": (fail_cost_all / total_cost * 100.0) if total_cost else None,
        "retry_tax": (fail_cost / total_cost * 100.0) if total_cost else None,
        "cache_share": (cached_tokens / input_tokens * 100.0) if input_tokens else None,
        "attempts_per_success": (attempts_on_success / successful) if successful else None,
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "duration_min": duration,
    }


def write_report(tasks, path):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "task_id", "attempts", "solved", "cost_usd", "cost_complete", "input_tokens",
            "cached_tokens", "output_tokens", "tool_calls", "duration_min",
        ])
        for task_id, attempts in tasks.items():
            writer.writerow([
                task_id,
                len(attempts),
                "yes" if any(a["outcome"] == "success" for a in attempts) else "no",
                f"{sum(a['cost_usd'] for a in attempts):.4f}" if all(a['cost_usd'] is not None for a in attempts) else "",
                "yes" if all(a['cost_usd'] is not None for a in attempts) else "no",
                int(sum(a["input_tokens"] for a in attempts)),
                int(sum(a["cached_tokens"] for a in attempts)),
                int(sum(a["output_tokens"] for a in attempts)),
                int(sum(a["tool_calls"] for a in attempts)),
                f"{sum(a['duration_min'] for a in attempts):.1f}",
            ])


def fmt(value, pattern="{:.4f}"):
    return "n/a" if value is None else pattern.format(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--out", default=None, help="write per-task report to this CSV")
    parser.add_argument("--review-rate", type=float, default=None,
                        help="cost per hour of manual review, in the same currency as cost_usd")
    args = parser.parse_args()

    if args.review_rate is not None and args.review_rate < 0:
        parser.error("--review-rate cannot be negative")
    tasks, unknown_cost_rows = load(args.csv_path, args.review_rate)
    if not tasks:
        sys.exit("No rows with task_id found — nothing to report.")

    s = summarize(tasks, args.review_rate)
    incomplete = unknown_cost_rows > 0
    caveat = f" (PARTIAL — {unknown_cost_rows} attempt(s) have no recorded cost)" if incomplete else ""

    print(f"Tasks:            {s['tasks']} ({s['successful']} solved, "
          f"{s['tasks'] - s['successful']} not solved)")
    print(f"Attempts:         {s['total_attempts']}")
    print(f"Measured cost:    ${s['total_cost']:.4f}{caveat}")
    if args.review_rate is not None:
        print(f"Review cost:      ${s['review_cost']:.4f} (@ ${args.review_rate:.2f}/h)")
        print(f"Total:            ${s['grand_total']:.4f}{caveat}")
    print(f"Cost per attempt: ${fmt(s['cost_per_attempt'])}{caveat}")
    if s["cost_per_success"] is None:
        print("Cost per successful task: undefined — 0 tasks met the success criterion")
    elif incomplete:
        print(f"Cost per successful task: ${s['cost_per_success']:.4f}{caveat} — "
              f"do not publish as a complete figure")
    else:
        print(f"Cost per successful task: ${s['cost_per_success']:.4f}")
    print(f"Failed attempts:  {fmt(s['failed_attempts_share'], '{:.1f}%')}{caveat} of spend went to attempts that failed "
          f"(some of those tasks later succeeded)")
    print(f"Retry tax:        {fmt(s['retry_tax'], '{:.1f}%')}{caveat} of spend went to tasks that never succeeded")
    print(f"Cache share:      {fmt(s['cache_share'], '{:.1f}%')} of input tokens were cache hits")
    print(f"Attempts/success: {fmt(s['attempts_per_success'], '{:.2f}')}")
    print(f"Wall-clock:       {s['duration_min']:.1f} min total, "
          f"{s['duration_min'] / s['total_attempts']:.1f} min per attempt")

    if unknown_cost_rows:
        print(f"\nWarning: {unknown_cost_rows} row(s) had no cost_usd — "
              f"treated as 0. Add costs before publishing numbers.")

    print("\nLimits to state next to these numbers:")
    print("  · one repo / one setup / one model — not a benchmark")
    print("  · 'success' is your own criterion (tests, review), not an objective truth")
    print("  · task boundaries are a judgement call; retries depend on where you cut them")
    if s["successful"] and s["successful"] < 10:
        print("  · fewer than 10 solved tasks: publish as a method, not as a benchmark")

    if args.out:
        write_report(tasks, args.out)
        print(f"\nPer-task report written to {args.out}")


if __name__ == "__main__":
    main()
