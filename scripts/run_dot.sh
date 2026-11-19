#!/usr/bin/env bash
# One command: build, run on Spike, count instructions, apply the cost model, make plots (DOT4).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results/dot4
python3 tests/gen_dot_vectors.py > /dev/null
./scripts/build.sh bench_dot bench/bench_dot.c kernels/dot/dot.c
./scripts/build.sh dot4_test tests/dot4_test.S
./scripts/run.sh dot4_test dot4
./scripts/run.sh bench_dot dot4
python3 scripts/analyze.py bench_dot dot_baseline dot_custom > build/bench_dot_counts.csv
python3 scripts/model.py bench_dot dot_baseline dot_custom dot4
python3 scripts/plots.py bench_dot DOT4 dot4
# Stronger baseline: the same comparison against a 4x-unrolled loop
./scripts/build.sh bench_dot_unroll bench/bench_dot_unroll.c kernels/dot/dot.c
./scripts/run.sh bench_dot_unroll dot4 > /dev/null
python3 scripts/analyze.py bench_dot_unroll dot_baseline_unroll4 dot_custom > build/bench_dot_unroll_counts.csv
python3 scripts/model.py bench_dot_unroll dot_baseline_unroll4 dot_custom dot4
python3 scripts/plots.py bench_dot_unroll DOT4 dot4
echo "results: results/dot4/bench_dot_results.csv, plots: results/dot4/plots/ (also bench_dot_unroll_*)"
