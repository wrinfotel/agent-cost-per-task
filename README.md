# agent-cost-per-task

What does one successfully completed task actually cost a coding agent?

Per-call and per-token prices don't answer that. This does: total spend on every attempt,
failed ones included, divided by the tasks that met a criterion you wrote down in advance.
Call it cost per successful task.

Small script, standard library only, runs on your own log.

## Definitions

**Attempt.** One agent run from start until it stops, or until you stop it.

**Outcome.** `success` or `fail`, judged by your pre-registered criterion: tests green,
review passed, spec item done. Not "looks good to me".

**Cost per attempt.** Total measured cost divided by the number of attempts.

**Cost per successful task.** Total measured cost divided by the number of tasks that
succeeded. Failures and retries stay in the numerator, on purpose.

If zero tasks succeed, that figure is undefined and the script says so instead of dividing
by zero.

## Quickstart

```bash
python3 parse.py sample.csv                    # demo data, 12 tasks
python3 parse.py mylog.csv --out report.csv    # your log
python3 parse.py mylog.csv --review-rate 25    # add $25/h of manual review to the total
```

Input CSV columns:

```
task_id,outcome,attempt_no,input_tokens,cached_tokens,output_tokens,tool_calls,duration_min,cost_usd
```

A longer schema works as-is too. The script accepts `attempt_outcome` for `outcome`,
`cached_input_tokens` for `cached_tokens` and `measured_cost_usd` for `cost_usd`, and it
ignores `task_final_outcome`, `tool_cost_usd`, `model` and `date` if you have them.

One row per attempt, several rows can share a `task_id`. Leave `cost_usd` empty when you
don't know it: every cost figure then comes out marked PARTIAL, with a note not to publish
it as complete. Silently reading missing cost as zero is how you get a confident number
that isn't true.

## The two failure numbers

The report prints both, because they answer different questions and people mix them up.

- **Failed attempts share.** How much of the spend went to attempts that did not succeed
  themselves. In the demo log that is 51.6%, including attempts that were later rescued by
  a retry.
- **Retry tax.** How much of the spend went to tasks that never succeeded at all. In the
  demo log, 20.1%. This is the number for "what did outright failure cost me".

Neither is a measure of waste. A failed attempt often hands the next one the context it
needed.

## What stays out of the headline

Subscription fees on flat monthly plans are not converted into per-token prices. Report
them separately, or state how you allocated a share of the fee.

Infrastructure, electricity and your own machine time: separate line, or omitted.

Manual review time is included only when you pass `--review-rate`, and it is labelled as an
assumption when it is.

Tasks abandoned mid-flight still count as attempts. They cost money whether or not they
produced a result.

## Limits to put next to your numbers

Anyone reading your figures will check this list, so put it in the post before they ask:

- one repo, one setup, one model, one window. Not a benchmark.
- the task set is small and hand-picked, so don't generalise from it;
- "success" is a judgement. The criterion was fixed in advance, but it is still yours, and
  tests plus review are imperfect;
- task boundaries are a call you make, and retry counts move depending on where you cut them;
- fewer than 10 solved tasks: publish it as a method, not as a benchmark.

## Why this exists

Public comparisons tend to measure what a model can do once. The bill is usually driven by
something else: retries, bad tool calls, re-runs. Dashboards that report spend per call
hide exactly that, which is why the gap between cost per attempt and cost per successful
task is worth knowing for your own setup.

Worth reading before trusting any coding benchmark: METR on measuring long tasks, NIST
CAISI on flaws in agent evaluations, and OpenAI's audit of SWE-bench Pro from July 2026,
which estimates roughly 30% of its tasks are broken.

## Files

`parse.py` is the parser and report. `sample.csv` is demo data so anyone can verify the
script without sharing a real log, and `report.csv` is its per-task output. The task set
and criteria template is in `tasks-and-criteria.md`.

## License

MIT. Your numbers stay yours.
