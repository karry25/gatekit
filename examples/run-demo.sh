#!/usr/bin/env bash
# gatekit demo: run the tools against the fictional weatherd project.
# Everything below really executes; outputs are not mocked.
set -u
cd "$(dirname "$0")"

echo '=== 1. brief: orient an AI in one paste ==='
python3 ../bin/brief demo-repo
echo
echo '=== 2. weatherd works (its own proof command) ==='
(cd demo-repo && python3 -m unittest discover -s tests 2>&1 | grep -E '^(OK|FAILED|Ran)')
echo
echo '=== 3. preflight: the pre-ship gate catches the planted problems ==='
python3 ../bin/preflight demo-repo --run-checks
rc=$?
echo
echo "preflight exit code: $rc (1 = blocked by the planted fake token, as intended)"
