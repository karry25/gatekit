# retro

## Purpose

Close the loop after a work period so the same mistakes stop repeating. The
failure mode this prevents is flat learning: shipping week after week while
the same class of bug, the same estimation error, and the same skipped step
keep coming back because nobody wrote them down.

## Inputs

- `PERIOD`: the time span under review (this week, this sprint, this build).
- `WORK LOG`: what actually happened - commits, shipped work, things that
  broke, things that got stuck. Facts, not feelings.

## Procedure

1. **Facts first.** List what shipped, what broke, and what is stuck, with
   dates. If the log is thin, reconstruct it from commits and messages
   before judging anything.
2. **Find the repeated pattern.** One-off bad luck is not a lesson. Look
   for the class: the third underestimation, the second skipped test, the
   recurring "I'll remember that" nobody remembered. Name the pattern in
   one sentence.
3. **Keep / stop / start.** At most three of each. Every item must be
   actionable: "stop merging after midnight" is actionable; "be more
   careful" is not.
4. **Feed it forward.** Each "stop" item becomes a line in the checklist or
   workflow you actually use - ship-check, plan-lock, wherever it would have
   been caught. A lesson that lives only in the retro is a lesson lost.
5. **Close the period.** State plainly whether the trend is better, worse,
   or flat versus the last retro, and why.

## Evidence

- The fact list (shipped / broke / stuck) with dates.
- The named pattern, or an honest "no pattern this period."
- The keep / stop / start table.
- The workflow lines added or changed as a result.

## Stop conditions

- No blame narrative. Facts and systems only - a retro that assigns fault
  instead of finding the weak step will be gamed next time.
- "Nothing to change" is a valid retro. Do not manufacture insights for an
  uneventful period.
- If the same stop-item appears three periods running, the problem is the
  follow-through, not the item. Say that out loud and change where the
  lesson lives.
- Do not use the retro to re-litigate decisions that were made with the
  information available at the time. Judge the process, not the past's
  knowledge.
