# second-opinion

## Purpose

Get a genuinely independent review from a different AI than the one that
wrote the code or plan. The failure mode this prevents is grading your own
homework: the model that produced the work is the worst reviewer of it,
because it shares the same blind spots and already "knows" what it meant.

## Inputs

- `ARTIFACT`: the diff, plan, or document to review (paste it in full).
- `REVIEWER`: a different AI or model than the author. State which is which.
- `CONTEXT`: the requirements the artifact was built against - nothing else.

## Procedure

1. **Strip the authorship cues.** Give the reviewer the artifact and the
   requirements. Do not include the author's explanation, confidence, or
   reasoning - those anchor the reviewer to the author's framing.
2. **Demand findings, not vibes.** Ask for issues ranked by severity, each
   with the exact location (file, line, or section) and the failure it
   would cause. Reject "looks good overall" as a non-answer.
3. **Require the unchecked list.** Every review must end with what the
   reviewer could not verify: things requiring execution, private context,
   or domain facts it lacks. A review without an unchecked list is
   overconfident by construction.
4. **Triage in the original session.** Bring the findings back and decide
   each one: ACCEPT (fix it), REJECT (with the reason), or DEFER (with the
   trigger that reopens it). No silent drops.
5. **Re-prove after changes.** Whatever the fix touches, re-run the checks
   that cover it. A review-driven fix is still a change; it needs evidence
   like any other.

## Evidence

- The reviewer's findings with severities and locations.
- The reviewer's unchecked list.
- Your triage decision per finding, with reasons.
- Post-fix check results for anything changed.

## Stop conditions

- A reviewer that agrees with everything is a red flag, not a pass. Push
  once with specific adversarial questions ("what breaks under concurrent
  writes?", "what happens when this input is empty?") before accepting
  silence.
- Never paste secrets, credentials, or private user data into a second
  service to get the review. Redact first; if redaction guts the artifact,
  do not send it.
- If the two AIs disagree about behavior owned by someone else (a spec, an
  API contract), escalate to the owner instead of picking the answer you
  prefer.
- The reviewer is a critic, not an authority. Its findings are input to
  your judgment, never an automatic command to change the work.
