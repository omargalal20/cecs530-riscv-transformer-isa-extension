#!/usr/bin/env bash
# Usage: scripts/run.sh <name> [extension names...]
# Runs build/<name>.elf on Spike with our plugins and writes the instruction trace to build/<name>.log
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
name="$1"; shift
exts=()
for e in "${@:-dot4}"; do exts+=("--extension=$e"); done
"$ROOT/third_party/install/bin/spike" --isa=rv32imf \
  --extlib="$ROOT/third_party/install/lib/libcustomext.so" "${exts[@]}" \
  -l --log="$ROOT/build/$name.log" "$ROOT/build/$name.elf" | tee "$ROOT/build/$name.out"
