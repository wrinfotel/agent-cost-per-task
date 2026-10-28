# Task set and success criteria — fill this in BEFORE the run

The point is to produce a number that cannot be accused of being fitted after the fact.

## 1. Run frame (fill in advance)

- agent: ...
- model and version: ...
- dates: from ... to ...
- repository / project type: ...
- agent internet access: yes / no
- attempt limit per task: ...
- pricing model (subscription / per token): ...
- what counts as one attempt: ...

## 2. The task set

Rules:

- **10-20 tasks.** Fewer than 10 solved -> publish a *method*, not a benchmark.
- **Publishable tasks only:** no secrets, no private code, no client data.
- **Mixed by size:** 4-5 small (one-file edit), 6-8 medium (several files, a test),
  2-3 large (refactor, new feature).
- **Mixed by type:** bug fix, adding a test, refactoring, dependency update, error
  handling, interface change.
- **Machine-checkable criteria where possible:** a test command, a linter, a build.
  Where that is impossible, write down in advance what "done" means.

Template:

| # | Task | Type | Size | Success criterion (checkable) | Attempts planned |
|---|---|---|---|---|---|
| t1 | | bug fix | S | `pytest tests/test_x.py` green | 1 |
| t2 | | test | S | test fails before the change, passes after | 1 |
| ... | | | | | |

## 3. What to record per attempt

`task_id, outcome, attempt_no, input_tokens, cached_tokens, output_tokens, tool_calls, duration_min, cost_usd`

- `outcome` — only `success` / `fail`, judged by the criterion from the table above.
- `cost_usd` — from the provider export/dashboard, or computed from the model price.
  Unknown price: leave it empty; the script will warn you instead of pretending.
- `cached_tokens` — the number readers care about most: how much input came from cache.
- `duration_min` — wall clock, not "model time".
- Keep manual review time separately (it is not in the CSV) and include it only via
  `--review-rate N`, so it shows up as an explicit assumption.

## 4. After the run

```bash
python3 parse.py mylog.csv --out report.csv
```

Check that:

- no rows in the report have a missing `cost_usd` — otherwise the number is not trustworthy;
- solved tasks >= 10, otherwise the write-up says "method", not "benchmark";
- the per-task report sums to the headline number in your post — it is the first thing
  a reader will verify.

## 5. What to publish next to the number

- how many tasks, how many attempts, how many solved;
- your success criterion in your own words;
- retry tax (share of spend on failed attempts) and cache share;
- limits: one repository, one model, small sample, task boundaries are your own call;
- the question you want answered back.
