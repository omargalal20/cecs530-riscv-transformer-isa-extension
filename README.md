# cecs530-riscv-transformer-isa-extension

Custom RISC-V ISA extensions that accelerate Transformer primitives.
Semester project for **CECS 530 – Advanced Computer Architecture** (CSULB).

**Team:** Michelle Luu · Omar Elhanafy · Johnny Van

**Status:** 🚧 Early setup. Decisions marked **TBD** below are still open.

---

## What this project does

Designing and evaluating custom RISC-V instructions to accelerate important Transformer operations, add them to a simulator, and measure how much they help compared to standard RISC-V.

1. **Design** custom instructions (name, encoding, behavior).
2. **Implement** them for at least two Transformer primitives in a simulator.
3. **Run** the same kernels two ways: baseline RISC-V (RV32IM) and with our custom instructions.
4. **Measure** execution cycles, instruction count and speedup, then analyze the results.

## Current decisions

| Decision | Status |
| --- | --- |
| Baseline ISA | RV32IM (base integer + multiply/divide) |
| Primitives | Leaning DOT4 (int8 dot-product-accumulate) + GELU. LayerNorm is a fallback or stretch. **TBD** |
| Data type | **TBD** (int8 only, or also fixed-point/float for GELU) |
| Simulator | Leaning Spike. Variant (C++, PySpike, or own interpreter) **TBD** |
| Cycle measurement | Modeled: instruction counts plus a documented latency model. **TBD** pending instructor confirmation |

## Proposed repository structure (planned, will change)

```text
cecs530-riscv-transformer-isa-extension/
├── README.md
├── docs/        # ISA spec, design notes, setup guide
├── isa/         # instruction definitions and encodings
├── kernels/     # baseline and custom kernels, one folder per primitive
├── tests/       # correctness tests against a Python reference
├── bench/       # run scripts and cycle model
├── results/     # raw data and figures
└── scripts/     # setup and helper scripts
```

Folders are created as we need them. Simulator location **TBD**.

## Getting started

**TBD** – toolchain and simulator setup steps go here once the simulator is chosen.

## How to run

**TBD** – build and run commands for baseline vs. custom kernels.

## Results

**TBD** - writing up the results

## Team workflow

- Work on a branch, open a pull request, and have a teammate review before merging to `main`.
- Keep commits small and messages descriptive.
- Large raw simulator traces are not committed (see `.gitignore`). Results and figures are.
