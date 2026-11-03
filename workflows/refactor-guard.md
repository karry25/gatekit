# refactor-guard

## Purpose

A protocol for changing code without changing behavior. Refactors fail in a
specific way: the code gets cleaner, the tests still pass, and a behavior
nobody had pinned down quietly changes. This protocol pins behavior first,
then moves the code.

## Inputs

- `TARGET`: the code you want to restructure, and why.
- `SCOPE`: the boundary - which files/modules may change, which must not.

## Procedure

1. **Pin the current behavior.** Before touching anything, write
   characterization tests: tests that record what the code does today,
   including the ugly parts (edge cases, weird error handling, accidental
   features someone may depend on). If the code has no seams for testing,
   the first refactor is adding seams - nothing else.
2. **List the dependents.** Grep for every caller, importer, and config that
   touches `TARGET`. Anything outside `SCOPE` that depends on it is a
   constraint, not a surprise to discover later.
3. **Move in small, green steps.** Each step: one mechanical change
   (rename, extract, move), run the pinned tests, confirm green, commit.
   Never stack two structural changes into one step. When a step goes red,
   undo that step - do not debug forward through a stacked diff.
4. **Separate behavior changes on purpose.** If you discover you also want
   to change what the code does, that is a different commit - after the
   refactor lands green, with its own test showing the intended change.
5. **Prove the boundary.** At the end, show the pinned tests still pass
   unmodified, and show the dependent list with how each was verified.

## Evidence

- The characterization tests, written before any restructuring.
- The step list, one mechanical change per step, each shown green.
- Proof no test was edited to make a step pass.
- The dependents list and their verification.

## Stop conditions

- Never edit a test and the code it tests in the same step. If both need
  changing, you are doing a behavior change - stop and split it.
- If a step goes red and you cannot say exactly why within a few minutes,
  revert the step. Do not patch forward.
- If you find the current behavior is itself a bug, note it and keep
  refactoring to preserve it anyway. Fixing it is a separate, visible
  change with its own review.
- If the code has no tests and no seams, do not start restructuring. Build
  the characterization net first, even if that is the whole session.
