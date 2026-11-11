#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .artifacts
rm -f .artifacts/localflow-bin-*.pkg.tar.zst
docker build --pull -t localflow-bin-check .ci
docker run --rm \
  -v "$PWD:/repo:ro" \
  -v "$PWD/.artifacts:/out" \
  localflow-bin-check
if [[ ${1:-} == --refresh-srcinfo ]]; then
  cp .artifacts/.SRCINFO .SRCINFO
else
  diff -u .SRCINFO .artifacts/.SRCINFO
fi
