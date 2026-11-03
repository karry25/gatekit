# plan-lock

## Purpose

Turn an approved direction into a locked implementation plan before any code
is written. The failure mode this prevents is plan drift: code that grows
organically from the first file, with architecture nobody chose, edge cases
nobody listed, and a test strategy invented after the bugs.

Run it after idea-stress has validated the wedge, before the first commit.

## Inputs

- `GOAL`: what this build must do when finished, in one paragraph.
- `NON-GOALS` (optional): what it explicitly will not do this round.
- `CONSTRAINTS`: stack, time, permissions, existing systems it must fit.

## Procedure

1. **Restate the goal and the non-goals.** If `NON-GOALS` is empty, propose
   three and ask which hold. A plan without non-goals has no edge.
2. **Surface the hidden assumptions.** List everything the plan depends on
   that is not yet verified: an API's actual capabilities, a permission, a
   data format, a rate limit, a cost. Mark each VERIFIED or UNVERIFIED.
   Every UNVERIFIED item becomes task zero, ordered before the work that
   depends on it.
3. **Choose the architecture on purpose.** Components, data flow, state,
   error paths. Draw the data flow as ASCII. Name the two biggest design
   decisions and the rejected alternative for each, with the reason.
4. **List the edge cases and failure modes.** Empty input, huge input,
   network down mid-write, duplicate submission, clock skew, whatever this
   system can actually meet. Each gets a chosen behavior, not "handle it."
5. **Write the test matrix first.** A table: behavior, the test that proves
   it, and what breaks if the test is missing. If a behavior has no possible
   test, the design is wrong - fix the design now.
6. **Order the work in verifiable steps.** Each step ends green with its
   own evidence. First step proves the riskiest assumption, not the easiest
   file.

## Evidence

- The assumptions list with VERIFIED / UNVERIFIED status.
- The data-flow diagram and the two named design decisions with rejected
  alternatives.
- The edge-case list with chosen behaviors.
- The test matrix.
- The ordered step list, each with its green condition.

## Stop conditions

- Do not write implementation code inside this workflow.
- An UNVERIFIED assumption that the whole plan rests on is not a risk to
  note - it is the next thing to check before planning further.
- If the plan requires changing a contract, schema, or system someone else
  owns, that change is a separate conversation with its owner, not a step
  you schedule silently.
- If you find yourself planning a feature nobody asked for, stop. It goes
  on the non-goals list or into a new idea-stress.
