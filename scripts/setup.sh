#!/usr/bin/env bash
# Build Spike at the pinned commit with our custom-instruction plugins.
# Safe to re-run: it skips steps that are already done.
set -euo pipefail

SPIKE_COMMIT=4c6a9bc79dab80616932949707e7c0471d8e9e54
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/third_party/riscv-isa-sim"
PREFIX="$ROOT/third_party/install"
PLUGINS="$ROOT/patches/riscv-isa-sim/customext"

# 1. Get Spike at the pinned commit (shallow fetch, plus the softfloat submodule)
if [ ! -d "$SRC/.git" ]; then
  mkdir -p "$SRC"
  git -C "$SRC" init -q
  git -C "$SRC" remote add origin https://github.com/riscv-software-src/riscv-isa-sim.git
fi
if [ "$(git -C "$SRC" rev-parse HEAD 2>/dev/null || true)" != "$SPIKE_COMMIT" ]; then
  git -C "$SRC" fetch --depth 1 origin "$SPIKE_COMMIT"
  git -C "$SRC" checkout -q FETCH_HEAD
fi
git -C "$SRC" submodule update --init --depth 1

# 2. Copy our plugin sources into Spike's customext folder and make them the only sources of
#    the plugin library. Spike's stock file bundles a full copy of Spike into the library
#    (300 MB) and its dummy_rocc.cc needs symbols Spike does not export; either one makes
#    Spike abort when it loads the library. So we write the file ourselves.
MK="$SRC/customext/customext.mk.in"
{ echo "customext_subproject_deps ="; echo; echo "customext_srcs = \\"; } > "$MK"
for f in "$PLUGINS"/*.cc; do
  name="$(basename "$f")"
  cp "$f" "$SRC/customext/$name"
  printf '\t%s \\\n' "$name" >> "$MK"
done
{ echo; echo "customext_install_shared_lib = yes"; } >> "$MK"

# 3. Configure, build, install
mkdir -p "$SRC/build"
cd "$SRC/build"
../configure --prefix="$PREFIX" > /dev/null
rm -f libcustomext.so   # force a relink when the plugin list changed
make -j"$(nproc)"
make install

echo "Done. Spike: $PREFIX/bin/spike   Plugins: $PREFIX/lib/libcustomext.so"
