# test-sweep

## Purpose

Audit an existing test suite for tests that cost more than they protect. Test
suites rot: they accumulate duplicates, tautologies, and probes that assert
nothing, and every useless test is paid for on every CI run and every
refactor. This is a report-first audit - it changes nothing without approval.

## Inputs

- `SUITE`: path to the tests, or the whole repo if tests live beside code.
- `FOCUS` (optional): a subsystem to prioritize.

## Procedure

1. **Map the suite.** Count tests per area. Note what is tested heavily and
   what is not tested at all. The gaps are as interesting as the waste.
2. **Find assertion-free tests.** Tests that run code but assert nothing
   (or only assert "it did not throw"). Each one proves only that the code
   executes on a happy path.
3. **Find source-grep tests.** Tests whose assertions just restate the
   implementation ("calls helper X", "contains string Y from the source").
   They break on every refactor and catch no bugs.
4. **Find duplicates.** Tests that would all fail together and all pass
   together. Keep the clearest one, flag the rest.
5. **Find test-only scaffolding.** Exports, flags, and code paths that exist
   only to make a test pass. Each is a design smell worth a note.
6. **Score and rank.** For every candidate: what it costs (runtime,
   maintenance), what it protects (what bug class it would catch), and a
   recommendation: KEEP, MERGE, REWRITE, or DELETE.

## Evidence

Every candidate gets an evidence card:

- File and test name.
- Why it is suspect, quoting the actual assertion (or its absence).
- What would break in the suite if it were removed.
- The recommendation and its reason.

## Stop conditions

- **Report only, by default.** Present the ranked list. Delete or rewrite
  tests only after the owner approves a specific batch.
- Never remove the only test covering a behavior, however ugly it is.
  Rewrite it instead, and show the rewrite keeps the same failure coverage.
- If you cannot tell what a test protects, that is a finding (undocumented
  intent), not permission to delete it.
- Removing a test to make a failing suite green is forbidden. That is the
  opposite of this audit.
