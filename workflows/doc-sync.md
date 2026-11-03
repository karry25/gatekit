# doc-sync

## Purpose

Check whether the docs still describe the software after a change. Docs rot
silently: the README promises a flag that was renamed, the setup guide
references a deleted script, the example output is three versions old. Run
this on every ship, and standalone when onboarding feels confusing.

## Inputs

- `CHANGE`: what changed (diff, release notes, or a description).
- `DOCS` (optional): which docs to check. Default: README plus anything that
  mentions a touched file, command, flag, or behavior.

## Procedure

1. **Extract the claims.** From `CHANGE`, list every user-visible claim that
   changed: commands, flags, config keys, file paths, behavior, output
   formats, requirements, defaults.
2. **Find every doc that touches a claim.** Grep the docs for each command,
   flag, path, and behavior. Docs that mention nothing changed are
   presumptively fine; docs that mention changed things are suspects.
3. **Verify each suspect line by line.** For every instruction: would this
   still work if a new user followed it exactly? Check commands exist, flags
   are spelled right, paths are real, and examples produce what is shown.
4. **Check the setup path specially.** The install/quickstart section is
   where new users live. Walk it as a fresh user would: every prerequisite
   named, every command runnable, no step assuming state from a previous
   project.
5. **Classify.** Each doc gets one of: UPDATED (fixed in this pass),
   CURRENT (checked, no changes needed), or BLOCKED (needs information you
   do not have - say exactly what).

## Evidence

- The claim list from the change.
- Per doc: the classification and the specific lines checked.
- For every UPDATED doc: the before/after of what you changed.
- The remaining gap list, even if empty.

## Stop conditions

- Do not document behavior you have not verified. If you cannot run it or
  read the code proving it, mark the doc BLOCKED with the missing check
  named - never write the plausible-sounding version.
- Do not delete a section because you do not understand it. Flag it.
- Changing a documented default, flag, or behavior without updating every
  doc that mentions it is exactly what this audit exists to catch - include
  your own diff in the suspects.
- If the code and the docs disagree and you cannot tell which is intended,
  that is a bug report, not a doc edit. Ask the owner.
