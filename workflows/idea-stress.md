# idea-stress

## Purpose

Stress-test a product or feature idea before code exists. The cheapest time
to discover you are building the wrong thing is before you build it. The
failure mode this prevents is polite agreement: an AI that validates every
idea and helps you build a beautiful thing nobody needs.

## Inputs

- `IDEA`: what you want to build, in your own words.
- `WHO` (optional): who you think it is for.
- `EVIDENCE` (optional): anything real you have - complaints, requests, your
  own repeated pain.

## Procedure

1. **Find the pain under the feature.** People describe solutions ("I want a
   dashboard") when they have a pain ("I keep missing stale events"). Ask
   what actually happens today, with specific recent examples, not
   hypotheticals. If there is no concrete pain story, that is the finding.
2. **Challenge the premises.** List every assumption the idea rests on
   (users have this problem, they will switch, the data exists, the API
   allows it, they will pay). For each: what is the evidence? Rank them by
   "if this is wrong, the whole thing dies."
3. **Name what already exists.** Search for existing tools, including the
   boring workaround people use now. "Nothing exists" usually means "I have
   not looked." State why the existing answer is not good enough - in the
   user's words, not yours.
4. **Find the narrowest wedge.** What is the smallest version that delivers
   the core value to one specific user? Cut everything that is not needed
   for that first "this is useful" moment. Estimate honestly: the full
   vision is usually months; the wedge should be days.
5. **Define the kill criterion.** What would you need to see, by when, to
   keep going? And what result means stop? Write it down now, while you are
   still honest.

## Evidence

- The concrete pain story (who, when, what happened).
- The premise list with per-premise evidence and a risk ranking.
- The existing-alternatives list and why each falls short.
- The wedge definition and the kill criterion.

## Stop conditions

- Do not write a single line of implementation code during this process.
- If the person with the pain cannot describe a specific recent instance,
  stop and get real examples before designing anything.
- If the wedge still requires an integration, permission, or dataset you do
  not have, the next step is securing that access - not building around the
  gap and hoping.
- "Everyone will want this" is not evidence. One named person with one
  painful story beats a market-size claim every time.
