# Changelog

## 0.3.0 - 2026-11-04

- New: app/ - gatekit studio, a local web app (stdlib-only server) with a
  real interface for preflight scans, repo briefs, the workflow library
  with a fill-in prompt composer, and local-only result ratings. Binds to
  127.0.0.1; read-only scans; --run-checks stays terminal-only.
- preflight/brief: Python check command is now picked from repo evidence
  (conftest.py, pytest config, declared pytest dependency, tests/ dir)
  instead of always suggesting pytest, which blocked unittest-only repos
  when pytest was missing. Found by independent review; regression-tested.
- brief: tree indentation now reflects real directory depth (first-level
  dirs no longer render above their own files). Found by independent
  review; regression-tested.
- preflight: files over 2 MB are reported by name as not scanned, and the
  CLEAR line says "partial scan" when any were skipped. Found by
  independent review; regression-tested.
- studio: answers loopback Host headers only (127.0.0.1 / localhost / ::1)
  with robust hostname+port parsing, closing the DNS-rebinding bypass of
  the local header check. Rejected zip uploads no longer leak temp
  directories; connections carry a 30s timeout so slow clients cannot tie
  up threads. Found by independent review; regression-tested.
- studio: corrupt or truncated zip uploads (bad CRC) now return a clean
  400 instead of dropping the connection, and their temp directory is
  removed. Found by independent review; regression-tested.
- 57 tests.

## 0.2.0 - 2026-11-03

- New workflows: plan-lock, second-opinion, retro. The set now covers the
  full build loop: Think, Plan, Build, Review, Test, Ship, Reflect.
- New tool: bin/brief - paste-ready repo briefing for chat-window AIs
  (stack, layout, key files, git state, proof commands).
- preflight: .env hygiene checks (tracked .env blocks; unignored .env
  warns), .preflightignore exclusion counts in reports, symlink-escape
  protection, explicit --run-checks trust-boundary notice.
- examples/: demo-repo and run-demo.sh, a real executed demo against a
  fictional project.

## 0.1.0 - 2026-11-03

- First milestone: six workflows (ship-check, bug-hunt, test-sweep,
  idea-stress, doc-sync, refactor-guard), bin/preflight, AGENTS.md digest.
