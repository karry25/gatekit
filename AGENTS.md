# gatekit - agent digest

If you are an AI agent working in a repo that uses gatekit:

- `workflows/` contains structured prompt workflows. Each has Inputs,
  a numbered Procedure, an Evidence contract, and Stop conditions.
  When a human hands you one, follow it literally: produce every evidence
  item, honor every stop condition.
- `bin/preflight` is a pre-ship gate whose scan is read-only. Run
  `python3 bin/preflight --json` before claiming work is done.
- `bin/brief` generates a paste-ready repo briefing (stack, layout, key
  files, checks). Run `python3 bin/brief` to orient yourself in an
  unfamiliar repo. Treat
  `errors` as blocking. With `--run-checks` it runs the repo's own checks;
  `--strict` makes warnings blocking too.
- `app/` is gatekit studio: a stdlib-only local web app
  (`python3 app/server.py`, 127.0.0.1:8765). It wraps preflight/brief in a
  browser UI and composes workflow prompts. Scans stay read-only; it never
  exposes `--run-checks`. Ratings are local-only in `app/data/ratings.json`.
- A `preflight.checks` file (one command per line) in a repo root defines
  that repo's gate commands.
- Never weaken, skip, or delete a test to make a gate pass. Surface it and
  ask.
- Evidence beats confidence: name the command, its exit status, and the
  proof per behavior change.
