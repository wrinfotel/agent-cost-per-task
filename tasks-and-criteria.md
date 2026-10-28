# Task set and success criteria: fill this in before the run

The whole point is a number nobody can accuse you of fitting afterwards. So write the
task list and the pass conditions down first, then run.

## 1. Frame of the run

- agent:
- model and version:
- dates: from ... to ...
- repository or project type:
- does the agent have internet access: yes / no
- attempt limit per task:
- pricing model: subscription or per token
- what counts as one attempt:

## 2. The task set

Ten to twenty tasks. Fewer than ten solved and you are publishing a method, not a
benchmark, so plan the write-up accordingly.

Publishable tasks only. No secrets, no private code, no client data, otherwise you can
never show the log.

Mix the sizes: four or five small ones (a single-file edit), six to eight medium (several
files plus a test), two or three large (a refactor, a new feature). Mix the types as well:
bug fix, test, refactor, dependency update, error handling, interface change.

Where you can, make the pass condition machine-checkable: a test command, a linter, a
build. Where you can't, write down in advance what "done" means, in your own words, and
hold yourself to it.

| # | Task | Type | Size | Success criterion | Attempts planned |
|---|---|---|---|---|---|
| t1 | | bug fix | S | `pytest tests/test_x.py` green | 1 |
| t2 | | test | S | fails before the change, passes after | 1 |
| | | | | | |

## 3. What to record per attempt

```
task_id, outcome, attempt_no, input_tokens, cached_tokens, output_tokens,
tool_calls, duration_min, cost_usd
```

`outcome` is only `success` or `fail`, decided by the criterion from the table above.

`cost_usd` comes from the provider export or dashboard, or from the model price. If you
don't know a price, leave the cell empty. The script marks all cost figures as partial and
tells you not to publish them as complete, which is better than being confidently wrong.

`cached_tokens` is the field readers ask about most, because context drives the bill far
more than generation does.

`duration_min` is wall clock, not time the model spent thinking.

Keep manual review time in your own notes rather than in the CSV, and bring it into the
report only through `--review-rate N`, so it shows up as a stated assumption.

## 4. After the run

```bash
python3 parse.py mylog.csv --out report.csv
```

Then check three things. No rows should have a missing `cost_usd`, or the number is not
trustworthy. Solved tasks should be ten or more, or the write-up says "method" instead of
"benchmark". And the per-task report should add up to the figure in your post, because
that is the first thing a reader will verify.

## 5. What goes in the post

How many tasks, how many attempts, how many solved. Your success criterion in your own
words. The failed-attempt share and the retry tax. The cache share if you have it. The
limits: one repository, one model, small sample, task boundaries are your call. Then the
question you want answered back, because that is what turns a number into a conversation.
