#!/usr/bin/env bash
# One command: build, run on Spike, count instructions, apply the cost model, make plots (DOT4).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tests/gen_dot_vectors.py > /dev/null
./scripts/build.sh bench_dot bench/bench_dot.c kernels/dot/dot.c
./scripts/build.sh dot4_test tests/dot4_test.S
./scripts/run.sh dot4_test dot4
./scripts/run.sh bench_dot dot4
python3 scripts/analyze.py bench_dot dot_baseline dot_custom > build/bench_dot_counts.csv
python3 scripts/model.py bench_dot dot_baseline dot_custom dot4
python3 scripts/plots.py bench_dot DOT4 dot4
echo "results: results/bench_dot_results.csv, plots: results/plots/"
