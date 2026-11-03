# gatekit

Engineering workflows that run anywhere you can paste a prompt, plus a
zero-dependency pre-ship gate for your repo.

gatekit is for students, solo builders, and anyone whose AI pair-programmer
is a chat window. The workflows are plain Markdown - copy one, fill in the
inputs, paste it into any AI. The `preflight` CLI is a single Python file
with no dependencies that checks your repo before you ship. No install
script, no hooks, nothing to configure.

Inspired by [gstack](https://github.com/garrytan/gstack) (MIT), Garry Tan's
engineering-team toolkit for coding agents. gstack goes much deeper:
dedicated agent-CLI integration, browser QA, and release automation across
many agent hosts. gatekit deliberately sits at the other end of the
spectrum - the smallest version of those ideas that works everywhere,
including a plain chat window with no tooling at all.

## What's inside

### Workflows (`workflows/`)

Each workflow is a structured prompt with inputs, numbered gates, an
evidence contract, and stop conditions. Together they cover the loop a real
build follows: Think (idea-stress) - Plan (plan-lock) - Build (bug-hunt,
refactor-guard) - Review (second-opinion) - Test (test-sweep) - Ship
(ship-check, doc-sync) - Reflect (retro). The evidence contract is the point:
the AI has to show its work, not just declare victory.

Workflows run in your own AI tool, so each run spends that tool's tokens
or credits. `preflight` and `brief` themselves cost nothing - their trust
boundary is spelled out below.

| Workflow | Use it when |
|----------|-------------|
| [ship-check](workflows/ship-check.md) | You think the work is done. Audits the full diff, runs the repo's checks, demands evidence per behavior change, and ends in a named verdict. |
| [bug-hunt](workflows/bug-hunt.md) | Something is broken. Root-cause-first debugging with a hypothesis log and a three-failed-fixes stop rule. |
| [test-sweep](workflows/test-sweep.md) | Your test suite feels bloated. Finds tests that cost more than they protect. Report-only unless you approve a batch. |
| [idea-stress](workflows/idea-stress.md) | Before you build. Challenges premises, finds existing alternatives, cuts the idea to its narrowest wedge, and writes the kill criterion. |
| [doc-sync](workflows/doc-sync.md) | After any ship. Checks whether the README and docs still describe the software, line by line. |
| [refactor-guard](workflows/refactor-guard.md) | Before restructuring. Pins current behavior with characterization tests first, then moves code in small green steps. |
| [plan-lock](workflows/plan-lock.md) | After the idea survives, before the first commit. Locks architecture, edge cases, a test matrix, and verifiable steps. Hidden assumptions become task zero. |
| [second-opinion](workflows/second-opinion.md) | After any significant diff or plan. Gets a genuinely independent review from a different AI, with findings ranked and triaged - not the author grading its own homework. |
| [retro](workflows/retro.md) | End of a week or a build. Facts first, the repeated pattern named, and every lesson fed back into the workflows that would have caught it. |

**How to use one:** open the file, copy everything, replace the `INPUTS`
with your specifics, paste into your AI of choice. Works in ChatGPT, Claude,
Gemini, or any coding agent. No setup.

### preflight (`bin/preflight`)

A single-file, stdlib-only Python CLI that runs a pre-ship gate on any repo.
The scan itself is read-only and makes no network calls; it never modifies
your project. The optional `--run-checks` flag executes the repo's own check
commands - those can do whatever they are written to do, so only use it on
code you trust.

```bash
# grab it
curl -o preflight https://raw.githubusercontent.com/karry25/gatekit/main/bin/preflight
chmod +x preflight

# scan: secrets, debug residue, project detection, suggested checks
./preflight

# also run the repo's own checks and block on failure
# (executes commands defined by the repo - only on code you trust)
./preflight --run-checks

# machine-readable, and treat warnings as failures
./preflight --json --strict
```

What it checks:

- **Secrets** (blocking): private key blocks, AWS keys, Google API keys,
  GitHub/Slack/Stripe/OpenAI-style tokens, JWTs. Placeholders and
  `os.environ`-style references are not flagged.
- **Possible credentials** (warning): heuristic `api_key = "..."` assignments.
  Quoted values only - unquoted assignments are not caught.
- **Oversize files**: files over 2 MB are not scanned, and the report says so
  by name instead of silently skipping them.
- **Debug residue** (warning): `console.log`, `debugger`, `pdb.set_trace()`,
  `binding.pry`. TODO/FIXME counts are reported as a note.
- **Project detection**: Node, Python, Go, Rust, Make - and prints the
  checks it suggests (`npm test`, `pytest`, ...). A `preflight.checks`
  file in your repo root (one command per line) defines your own gate and
  replaces auto-detection.
- **Git state**: branch, uncommitted files, upstream - informational.
- **`.preflightignore`**: one fnmatch pattern per line (matched against
  repo-relative paths) to exclude files from every scan - for fixtures,
  snapshots, or vendored examples.

Requires Python 3.8+. That's it.

### brief (`bin/brief`)

A chat-window AI cannot see your repository. `brief` fixes the start of every
session: one command builds a paste-ready briefing - stack, layout, key
files, git state, and the exact commands that prove the project works.

```bash
./bin/brief > context.md   # then paste context.md into your AI chat
```

Read-only, no network, no dependencies - same rules as preflight.

### studio (`app/`)

A local web app that puts a real interface on top of the tools. Run the
scans and briefs from your browser, browse the workflow library, fill in a
workflow's inputs and copy the composed prompt, and rate results to keep a
record of what worked.

```bash
python3 app/server.py        # then open http://127.0.0.1:8765
```

- Binds to 127.0.0.1 only. No CDNs, no analytics, nothing leaves your
  machine. Ratings live in `app/data/ratings.json`.
- Scans stay read-only: `--run-checks` is deliberately not exposed in the
  UI, because it executes repo-defined commands. Use the terminal for that,
  only on code you trust.
- You can scan a folder path or upload a .zip (extracted to a temp folder
  and deleted after the scan).

## Run it on your computer

You need Python 3.8 or newer (`python3 --version` to check). Nothing else to
install - no dependencies, no accounts.

```bash
# get the code: either clone it
git clone https://github.com/karry25/gatekit.git
cd gatekit
# ...or download the zip from the repo page (Code -> Download ZIP),
#    unzip it, and cd into the extracted gatekit folder

# prove it works (57 tests, ~2 seconds)
python3 -m unittest discover -s tests -v

# the pre-ship gate, checking gatekit itself
python3 bin/preflight .

# a paste-ready briefing of the repo for any AI chat
python3 bin/brief .

# the full demo against a fictional project with planted problems
bash examples/run-demo.sh

# the web app: scans, briefs, workflow library, ratings
python3 app/server.py
# then open http://127.0.0.1:8765 in your browser
```

Tested on Linux with Python 3.10. The studio app binds to 127.0.0.1 only
(your own computer, not the internet). Windows is untested; the CLIs should
work, the demo script and studio are bash/Unix-oriented.

A real executed demo - actual tool output plus a bug-hunt session following
the workflow verbatim - is in [examples/DEMO.md](examples/DEMO.md).

## Design rules

- **Evidence over confidence.** Every workflow and every gate ends in named
  proof, not a vibe. "Tests should pass" is a hypothesis.
- **Report before mutation.** Audits (test-sweep, doc-sync) are report-only
  until a human approves a specific batch.
- **Stop conditions are features.** Knowing when to ask a human is what
  makes an automated step trustworthy.
- **Plain files, no magic.** If a workflow stops serving you, edit the
  Markdown. There is no framework to fight.

## What gatekit is not

- Not a coding agent or an agent plugin. It runs wherever you already talk
  to an AI.
- Not a replacement for CI. `preflight` catches the embarrassing stuff in
  seconds; your real test suite still owns correctness.
- Not a security audit. The secret scan catches common token formats, not
  every leak (unquoted assignments and files over 2 MB are skipped - skips
  are reported by name). Treat a clean result as a floor, not a guarantee.

## Contributing

Small, focused contributions welcome - see [CONTRIBUTING.md](CONTRIBUTING.md).
The bar: a workflow must earn its place (would a good engineer actually run
this?), and `preflight` stays dependency-free.

## License

[MIT](LICENSE) - fork it, improve it, make it yours.
