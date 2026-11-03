# gatekit demo - real execution, 3 Nov 2026

Everything on this page actually ran. Tool outputs are pasted verbatim from
the terminal. The workflow report at the end was produced by an AI assistant
following `workflows/bug-hunt.md` verbatim; that is how a workflow demo works
- the workflow is a prompt, so the demo is a real session using it.

The subject is `examples/demo-repo/`, a fictional two-file weather CLI with
three planted problems: a fake token in `config.txt`, a leftover debug
print, and an unhandled unknown city.

## 1. brief - orient an AI in one paste

`python3 bin/brief examples/demo-repo` really returned:

```
# Repo brief: demo-repo

Context for an AI working on this repository. Paste this at the
start of the conversation.

## Stack
- python
- files by extension: .py x2, .md x1, .txt x1, .checks x1, .toml x1

## Layout
      README.md
      config.txt
      preflight.checks
      pyproject.toml
    src/
      weather.py
    tests/
      test_weather.py

## Key files
- README.md: present
- pyproject.toml: present
- preflight.checks: present

## Checks that prove this repo works
- `python3 -m unittest discover -s tests`

## Working agreement
- Run the checks above before calling any change done.
- Show evidence (test output, real results), not confidence.
```

## 2. preflight - the gate catches the planted problems

`python3 bin/preflight examples/demo-repo --run-checks` really returned
(exit code 1):

```
preflight 0.2.0 - examples/demo-repo
  project: custom (preflight.checks)
  suggested checks:
    - python3 -m unittest discover -s tests
  [PASS] python3 -m unittest discover -s tests
  ERROR secret (JWT) at config.txt:3
  warn  possible-credential at config.txt:2
  note  1 TODO/FIXME markers across 1 files
  BLOCKED - fix the errors above before shipping.
```

The demo repo's own tests pass, the planted fake token blocks the ship, and
the suspicious config assignment is flagged for review. gatekit's own repo
stays clear because its `.preflightignore` excludes the planted file - and
says so in its report (`1 files excluded by .preflightignore`).

## 3. bug-hunt - a real session following the workflow

Trigger: `python3 src/weather.py paris` really failed with:

```
Traceback (most recent call last):
  File "src/weather.py", line 19, in <module>
    print(summarize(sys.argv[1]))
  File "src/weather.py", line 11, in summarize
    report = FAKE_DATA[city.lower()]
KeyError: 'paris'
```

Following `workflows/bug-hunt.md`:

1. **Symptom, precisely.** `weather.py paris` exits 1 with
   `KeyError: 'paris'` at `src/weather.py:11`. Any city outside the three
   hardcoded entries crashes the same way.
2. **Reproduced.** The command above fails identically every run, before
   any change.
3. **Data trace.** `sys.argv[1]` -> `summarize(city)` -> `FAKE_DATA[city.
   lower()]` at line 11. Reality diverges from expectation exactly there:
   the dict lookup assumes every input is a known city.
4. **Hypothesis log.**
   - H1: case sensitivity. Cheapest test: `weather.py LONDON` - passes
     (the tests already cover it). DEAD.
   - H2: unknown keys are unhandled. Test: `weather.py paris` - crashes.
     CONFIRMED at line 11.
5. **Fix + proof.** Replace the direct lookup with `.get()` and a friendly
   "unknown city" answer, add `test_unknown_city`, then prove both sides.
   The new test against the OLD code really failed:

   ```
   FAILED (errors=1) - KeyError: 'paris'
   ```

   The fixed code really runs clean:

   ```
   $ python3 src/weather.py paris
   paris: no data (try london, pune, tokyo)   # exit 0
   $ python3 -m unittest discover -s tests
   OK                                          # 3 tests
   ```

6. **Blast radius.** `FAKE_DATA` and `summarize` each have exactly one use
   site, verified by grep. No other path shares the assumption. Remaining
   known issue: the debug `print` on line 12 still writes internals to
   stdout. The scanner does not flag bare `print` calls (Python has too many
   legitimate uses) - it is tracked by the TODO marker preflight reported,
   not silently forgotten.

Verdict per the workflow: fix proven both directions, regression test in
place, blast radius checked, leftover issue named instead of hidden.

*(The fix and its test are intentionally NOT committed to demo-repo, so you
can run the same bug-hunt yourself.)*
