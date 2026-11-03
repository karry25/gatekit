# ship-check

## Purpose

A gate to run before any pull request or "it's done" claim. Its job is to stop
the two most common AI-assisted shipping failures: declaring victory without
evidence, and merging a diff nobody actually read end to end.

Use it when you think the work is finished, before you ask anyone else to look.

## Inputs

- `CHANGE`: one sentence describing what you changed and why.
- `DIFF`: the actual diff or list of touched files (paste it, or point the AI
  at the branch).
- `CHECKS`: the commands this repo uses to prove itself (tests, lint, build).

## Procedure

1. **Restate the change.** In one sentence, say what the code now does
   differently. If you cannot, stop - you are shipping something you do not
   understand.
2. **Read the whole diff.** Not the summary, the diff. For every hunk, answer:
   does this belong to `CHANGE`? Flag anything that snuck in (formatting
   sweeps, unrelated edits, commented-out code, leftover experiments).
3. **Run the repo's own checks.** Use `CHECKS`. Paste real output. "Should
   pass" is a hypothesis, not a result.
4. **Prove the new behavior.** For each behavior you added or changed, show
   one piece of evidence it works: a test that fails without your change, a
   before/after output, or a screenshot. If no test covers the change, say so
   explicitly instead of calling it green.
5. **Hunt the cheap mistakes.** Scan the diff for debug leftovers
   (`console.log`, `pdb`, `print` spam), secrets, dead code, and TODOs you
   introduced. (The `preflight` CLI in this repo automates this pass.)
6. **Write the verdict.** One of: SHIP (with the evidence list), FIX FIRST
   (with the blocking list), or NOT MINE (parts of the diff you cannot
   explain - ask before merging them).

## Evidence

A ship-check report is only valid if it contains:

- The check commands that ran and their real exit status.
- One piece of evidence per behavior change (test, output, or screenshot).
- The list of diff hunks that were not part of `CHANGE`, even if empty.
- The named verdict.

## Stop conditions

Stop and ask a human instead of proceeding when:

- A check fails and the fix would change behavior someone else owns.
- The diff contains changes you cannot explain the origin of.
- You weakened, skipped, or deleted a test to get green. Never do this
  silently; surface it by name.
- You are about to resolve a merge conflict in code you have not read.
