# bug-hunt

## Purpose

Root-cause-first debugging. The failure mode it prevents is fix-roulette:
changing plausible things until the error message goes away, which hides the
real bug and often ships two new ones.

## Inputs

- `SYMPTOM`: what is wrong, in observable terms (error text, wrong output,
  bad state) - not your theory about it.
- `REPRO`: how to make it happen, or the closest you have.
- `CONTEXT`: what changed recently, if anything.

## Procedure

1. **Write the symptom precisely.** "Login is broken" is not a symptom.
   "POST /login returns 500 with `KeyError: 'session'` since commit abc123"
   is. Rewrite `SYMPTOM` until it is observable.
2. **Reproduce before touching anything.** If you cannot reproduce it, your
   first job is building a reproduction, not guessing a fix. Say so if you
   are stuck here.
3. **Trace the data, not your intuition.** Follow the actual value from where
   it enters to where it breaks. Log or print the intermediate states. Name
   the exact line where reality first diverges from what you expected.
4. **Keep a hypothesis log.** Every theory gets one line: hypothesis, the
   cheapest test that would kill it, the result. Test the cheapest kill-shots
   first. Cross off dead theories instead of quietly abandoning them.
5. **Fix the cause, then prove it.** The fix must make your reproduction
   pass. Then write the smallest regression test that fails on the old code
   and passes on the new.
6. **Check the blast radius.** Grep for other call sites or code paths that
   shared the broken assumption. Either fix them or list them as known
   remaining risks.

## Evidence

- The reproduction steps and their before/after results.
- The hypothesis log, including the dead ends.
- The regression test and proof it fails on the old code.
- The blast-radius list, even if empty.

## Stop conditions

- **Three failed fixes.** If three attempted fixes have not worked, you are
  guessing. Stop, revert to the last clean state, and go back to step 3 with
  better tracing.
- The fix requires changing behavior owned by someone else, or a shared
  schema, API contract, or data migration.
- The "bug" turns out to be specified behavior. Confirm with whoever owns
  the spec before changing it.
- You are tempted to wrap the failing code in a blanket try/except to make
  the error go away. That is hiding the bug, not fixing it.
