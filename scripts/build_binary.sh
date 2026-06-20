#!/usr/bin/env bash
set -euo pipefail

rm -rf build dist manotron.spec

uv run pyinstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name manotron \
  --paths src \
  src/manotron/__main__.py

