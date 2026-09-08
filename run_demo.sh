#!/bin/sh
set -eu
cd "$(dirname "$0")"
OUT="$(mktemp -d ./outputs/demo-XXXXXX)"
python3 lucidecon.pyz demo --output "$OUT"
printf '\nResults: %s\n' "$OUT"
