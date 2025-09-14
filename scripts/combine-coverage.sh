#!/usr/bin/env bash
set -euo pipefail

python -m pip install coverage >/dev/null 2>&1 || true
coverage combine
coverage xml -o coverage.xml
coverage html -d htmlcov
echo "Combined coverage written to coverage.xml and htmlcov/"

