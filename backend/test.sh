#!/bin/bash
set -e

# Make sure we are in the script's directory
cd "$(dirname "$0")"

echo ">>> Building and starting test services..."
docker compose build test
docker compose up -d db redis

echo ">>> Running test suite..."
# If args are passed to this script, treat them as a full pytest invocation
# (e.g. `./test.sh wallet/tests/test_escrow_pytest.py -v`). With no args,
# run the default command (pytest --create-db).
if [ "$#" -gt 0 ]; then
  docker compose --profile test run --rm --entrypoint python test -m pytest "$@"
else
  docker compose --profile test run --rm test
fi
2