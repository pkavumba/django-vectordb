#!/usr/bin/env bash
set -euo pipefail

# Run full tox matrix quietly
exec tox -q "$@"

