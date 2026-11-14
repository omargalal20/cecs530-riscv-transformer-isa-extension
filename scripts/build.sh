#!/usr/bin/env bash
# Usage: scripts/build.sh <name> <source.c> [more sources...]   ->  build/<name>.elf
# One set of flags for every program, so baseline and custom are always compiled the same way.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
name="$1"; shift
mkdir -p "$ROOT/build"
riscv64-unknown-elf-gcc -march=rv32imf_zicsr -mabi=ilp32f -O2 -ffp-contract=off \
  -ffreestanding -nostdlib -nostartfiles -static -Wl,--no-warn-rwx-segments \
  -T "$ROOT/runtime/link.ld" "$ROOT/runtime/crt0.S" "$@" -lgcc -o "$ROOT/build/$name.elf"
echo "built build/$name.elf"
