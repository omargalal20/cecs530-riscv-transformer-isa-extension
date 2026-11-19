#!/usr/bin/env bash
# One command for GELU: build, test, run on Spike, count, model, plot. Same steps as run_dot.sh.
# Needs: kernels/gelu/gelu.c (gelu_baseline), (gelu_custom is in gelu.c),
#        bench/bench_gelu.c, tests/gen_gelu_vectors.py, tests/gelu_test.S, and the gelu plugin.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results/gelu
python3 tests/gelu_accuracy.py > results/gelu/gelu_accuracy.txt
python3 tests/gen_gelu_vectors.py > /dev/null
./scripts/build.sh bench_gelu bench/bench_gelu.c kernels/gelu/gelu.c
./scripts/build.sh gelu_test tests/gelu_test.S
./scripts/run.sh gelu_test gelu
./scripts/run.sh bench_gelu gelu
python3 scripts/analyze.py bench_gelu gelu_baseline gelu_custom > build/bench_gelu_counts.csv
python3 scripts/model.py bench_gelu gelu_baseline gelu_custom gelu
python3 scripts/plots.py bench_gelu GELU gelu
echo "results: results/gelu/bench_gelu_results.csv, plots: results/gelu/plots/"
