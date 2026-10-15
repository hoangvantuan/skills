#!/usr/bin/env bash
# Every test here runs offline against fixtures captured from a real tenant, so a change to
# the converter, the resolver or the preflight diagnosis can be checked without a tenant,
# without a live meeting, and without spending Graph calls.
set -uo pipefail
cd "$(dirname "$0")"
FAIL=0
for t in test_transcript_to_text.py test_meeting_resolver.py test_sharepoint_and_quality.py; do
  echo "== $t"; python3 "$t" 2>&1 | tail -3 || FAIL=1
  python3 "$t" >/dev/null 2>&1 || FAIL=1
done
echo "== test_preflight.sh"; ./test_preflight.sh || FAIL=1
[ "$FAIL" = 0 ] && echo "ALL GREEN" || { echo "SOMETHING FAILED"; exit 1; }
