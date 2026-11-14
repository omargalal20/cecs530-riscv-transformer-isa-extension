# Custom ISA Extensions for Transformer Primitives

**CECS 530 — Advanced Computer Architecture | CSULB Fall 2026 | Sec 01**

This repository contains the code, experiments and documentation for designing custom RISC-V instructions that accelerate Transformer operations. We add the instructions to the Spike simulator, run the same kernels with and without them, and compare instruction count and modeled execution cycles.

> **Status: early setup.** Toolchain and simulator setup are being verified. Sections marked **TBD** are open team decisions or not yet built. See [Project Status](#project-status).

---

## Research Question

> Which custom RISC-V instructions reduce the instruction count and modeled cycles of Transformer primitives the most, and how sensitive is that gain to the latency we assume for the new instruction?

**Objectives**
1. Define at least two custom instructions (name, binary encoding, exact behavior).
2. Implement them in Spike and call them from C kernels.
3. Run each kernel as a baseline (standard RV32IM) and as a custom version, and check both against a Python reference.
4. Measure instruction count, modeled cycles and speedup across input sizes.
5. Explain from a computer-architecture view where the gain comes from and what it costs.

**Expected outcome (hypotheses, not results).** A hand count for 4 int8 elements gives 28 baseline instructions (19 with 4x loop unrolling) against 6 with a fused dot-product instruction. Measured numbers will replace these. The gain for GELU depends on the data type and on how good the baseline approximation is, so it may be smaller.

## Background

| Term | Meaning |
|---|---|
| **ISA** | Instruction Set Architecture: the list of instructions a processor understands |
| **RV32I** | RISC-V base integer ISA, 32-bit, 40 instructions |
| **M extension** | Adds multiply and divide. Our baseline is **RV32IM** (base + M) |
| **ISA extension** | New instructions added on top of an ISA. Ours use the reserved `custom-0` opcode (`0x0B`) |
| **Kernel** | A small program that does one operation, such as a dot product |
| **Spike** | The RISC-V reference simulator: a program that behaves like a RISC-V CPU |
| **Speedup** | Baseline cycles ÷ custom cycles |
| **Amdahl's law** | Total speedup is limited by the fraction of runtime the improved part represents |

### Transformer primitives

| Primitive | Where it appears | What it computes |
|---|---|---|
| **Dot product** | Attention scores and every matrix multiply | Multiply pairs of numbers, then sum them |
| **GELU** | Feed-forward block | A smooth activation applied to each value |
| **LayerNorm** | Before or after each block | Rescale each vector to mean 0 and variance 1, then apply a learned scale and shift |

Standard RISC-V has no instruction for these, so each becomes a long chain of simple ones. A dot product needs 7 instructions per element (2 loads, multiply, add, 2 pointer updates, branch). GELU needs `tanh` or `erf`, which have no instruction. LayerNorm needs a square root and a division.

### Related hardware

Fused 8-bit dot products already exist elsewhere: Arm `SDOT`/`UDOT`, x86 `VPDPBUSD` (VNNI) and NVIDIA `dp4a` all multiply four 8-bit pairs and accumulate into 32 bits [7–9]. RISC-V has a vector draft, `Zvdot4a8i` (formerly `Zvqdotq`), whose ratification we could not confirm [10]. Our instructions are scalar and live in the `custom-0` slot. The contribution is the implementation and the measurements.

## Candidate Instructions

| ID | Instruction | Primitive | Status |
|---|---|---|---|
| `dot4` | int8 dot-product-accumulate over 4 packed pairs (accumulate form being designed) | Dot product | Leaning primary |
| `gelu` | GELU approximation (lookup table or piecewise-linear) | GELU | Leaning primary, data type **TBD** |
| `rsqrt` | Reciprocal square root | LayerNorm | Fallback or stretch |
| `requant` | int32 → int8: scale, shift, clamp | Quantization | Optional companion to `dot4` |

The brief requires at least two instructions. Fallback set: dot product, GELU and LayerNorm.

## Methodology

```
 kernel.c ──► GCC (RV32IMF) ──► program.elf ──► Spike (+ our instruction) ──► instruction counts ──► cost model (Python) ──► cycles, speedup, graphs
 (baseline | custom)

 Python reference ──► expected outputs ──► compared with the program's output (correctness)
```

**Simulator.** [Spike](https://github.com/riscv-software-src/riscv-isa-sim), pinned to commit `4c6a9bc` so all three of us build the same code. Spike is a functional simulator: it runs programs correctly but has no timing model. Its documented way to add an instruction is a behavior file plus an opcode entry in the Spike source tree [5]. Spike can also load instructions from a shared library with `--extlib`, which would let us leave Spike unmodified. We use the plugin route: our instructions live in `patches/riscv-isa-sim/customext/` and `scripts/setup.sh` builds them into a plugin library that Spike loads with `--extlib` and `--extension`.

**Cycle model.** Cycles are modeled, not measured: cycles = Σ (instruction count × assumed latency per instruction class). The latency table will live in `bench/`. We sweep the custom instruction's latency (for example 1 to 4 cycles) to show how sensitive the speedup is. Whether a modeled cycle count is acceptable is being confirmed with the instructor.

**Fair baseline.** The baseline is compiled with a reasonable optimization level and compared against loop-unrolled variants, so the speedup is not inflated.

**Metrics.** Instruction count, modeled cycles, speedup per input size, and correctness against the Python reference.

## Experimental Setup

| Item | Value |
|---|---|
| Baseline ISA | RV32IM |
| Compiler | GCC 13.2.0 for RISC-V bare metal (`gcc-riscv64-unknown-elf`, Ubuntu 24.04). Flags and optimization level **TBD** |
| Simulator | Spike, commit `4c6a9bc` |
| Custom opcode | `custom-0` (`0x0B`), R-type, assembled with `.insn` [6] |
| Data type | **TBD** |
| Kernels | Dot product, GELU (required); LayerNorm (fallback) |
| Input sizes | **TBD** |

## Repository Structure

```
.
├── README.md
├── .gitignore
├── docs/        (planned) ISA spec, design decisions, setup notes
├── isa/         (planned) instruction definitions and encodings
├── runtime/     (planned) bare-metal startup, linker script, console and counter helpers
├── kernels/     (planned) one folder per primitive: baseline and custom versions
├── sim/         (planned) Spike instruction plugin, if we use the plugin route
├── tests/       (planned) Python reference and test-vector generator
├── bench/       (planned) benchmark programs and the cycle model
├── scripts/     (planned) setup.sh, build and run helpers
├── results/     (planned) summary CSVs and figures
└── third_party/ , build/   Generated locally, not tracked by git
```

## Getting Started

Checked on Ubuntu 24.04 (WSL) and in a cloud Ubuntu 24.04 container: both give identical results.

### 1. Prerequisites

| Platform | Install |
|---|---|
| **Windows** | Install WSL 2 with Ubuntu 24.04 (`wsl --install -d Ubuntu-24.04`), then work inside the Linux filesystem (`~/`), not under `/mnt/c`. Follow the Ubuntu line below. |
| **Ubuntu 24.04** | `sudo apt update && sudo apt install -y build-essential git python3 python3-matplotlib device-tree-compiler libboost-regex-dev libboost-system-dev gcc-riscv64-unknown-elf` |
| **macOS** | Not yet tested |

Run `sudo apt update` first: a stale package list gives `404 Not Found` errors. Check the compiler: `riscv64-unknown-elf-gcc --version` (we used GCC 13.2.0; instruction counts can change with the compiler version).

### 2. Clone the repository

```bash
git clone https://github.com/omargalal20/cecs530-riscv-transformer-isa-extension.git
cd cecs530-riscv-transformer-isa-extension
```

### 3. Build Spike and our instruction plugins

```bash
./scripts/setup.sh
```

This fetches Spike at the pinned commit `4c6a9bc`, copies the plugin sources from `patches/riscv-isa-sim/customext/` into it, and builds everything into `third_party/install/`. The first run takes roughly 10 to 20 minutes; re-runs take a few minutes. It ends with `Done. Spike: ...`.

### 4. Run the DOT4 experiment

```bash
./scripts/run_dot.sh
```

Expect six `PASS` lines, then `results: results/bench_dot_results.csv, plots: results/plots/`. The row for n=1024 should read `rand_1024,1024,7173,1802,3.981,9220,2569,3.589`.

What the script does: builds the kernels, runs them on Spike with the DOT4 plugin, counts executed instructions from Spike's trace (`scripts/analyze.py`), applies the cost model (`scripts/model.py`, table in `model/latencies.json`) and draws the plots (`scripts/plots.py`).

### 5. Build and run your own program

```bash
./scripts/build.sh <name> <sources.c ...>     # writes build/<name>.elf
./scripts/run.sh <name> dot4                  # runs on Spike, trace in build/<name>.log
```

Pass one extension name per plugin, for example `./scripts/run.sh gelu_test dot4 gelu`.

### Adding a new instruction

1. Write `patches/riscv-isa-sim/customext/<name>.cc` (copy `dot4.cc` as a template).
2. Run `./scripts/setup.sh`. Every `.cc` file in that folder is built into the plugin.
3. Use the instruction from C with `.insn r ...` inline assembly (see `kernels/dot/dot.c`).
4. Add its mnemonic and a latency to `scripts/analyze.py` and `model/latencies.json`.

### Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `No rule to make target '../softfloat/softfloat_upstream.h'` | Spike's floating-point library is a git submodule that was not fetched. `setup.sh` fetches it; if you build by hand, run `git submodule update --init` inside `third_party/riscv-isa-sim`. |
| `Plugin "imsic_mmio" already registered` | The plugin library bundled a full copy of Spike. Re-run `./scripts/setup.sh`; it writes a minimal build file. `libcustomext.so` should be about 400 KB, not 300 MB. |
| `apt` says `404 Not Found` | Stale package list. Run `sudo apt update` and retry. |
| Spike hangs on a custom instruction | The plugin was not loaded. Pass the extension name to `scripts/run.sh`. |
| `unknown instruction '<x>'` from `analyze.py` | A new instruction needs an entry in `CLASSES` in `scripts/analyze.py`. |
| `no latency for instruction class '<x>'` | Add the class to `model/latencies.json`. |

## Results

Populated as runs complete. Full DOT4 results for all sizes are in `results/bench_dot_results.csv`.

| Kernel | Variant | Input size | Instructions | Modeled cycles | Speedup vs baseline | Correct |
|---|---|---|---|---|---|---|
| dot (int8) | baseline | 1024 | 7173 | 9220 | 1.00 | yes |
| dot (int8) | custom (DOT4, 2-cycle assumed) | 1024 | 1802 | 2569 | 3.59 | yes |
| GELU | baseline | — | — | — | 1.00 | — |
| GELU | custom | — | — | — | — | — |

## Project Status

Project due **Nov 20, 2026**. Presentations on **Nov 21** and **Dec 5, 2026**.

| Milestone | Status |
|---|---|
| Topic selected, team registered | Complete |
| Drive, repository and one-pager | Complete |
| Toolchain and Spike build verified | Complete |
| Baseline kernel running on Spike | Complete (DOT product) |
| Custom instruction running in Spike | Complete (DOT4); GELU in progress |
| Cycle model and experiments | Not started |
| Report and presentation | Not started |

## Open Decisions

| Decision | Options | Status |
|---|---|---|
| Data type | int8 only, or also fixed-point/float (needed for a fair GELU baseline) | **TBD** |
| Spike route | Source-tree change, `--extlib` plugin, or PySpike [11] | **TBD** (plugin route being tried first) |
| Final primitives | `dot4` + `gelu`, or a different pair; LayerNorm as stretch | **TBD** |
| Cycle measurement | Modeled cycles acceptable? | Pending instructor |
| Baseline compiler flags | `-O2` vs `-O3`, unrolling | **TBD** |

## Working Together

- Work on a branch named `type/short-topic` (for example `feat/dot4-encoding`), open a pull request, and have a teammate review before merging. No direct pushes to `main`, and no force-pushes to shared branches.
- Commit messages follow `type(scope): summary`, present tense, under about 72 characters.

| Type | Use for |
|---|---|
| `feat` | New instruction, kernel or simulator change |
| `fix` | Bug fix |
| `test` | Correctness tests |
| `bench` | Measurement scripts and the cycle model |
| `docs` | README, ISA spec, decision records |
| `chore` | Setup and housekeeping |

- Large traces and logs are not committed (see `.gitignore`). Summary CSVs and figures are.

## Limitations

- Cycles are modeled from instruction counts and an assumed latency table, not measured on a timing-accurate simulator or hardware.
- Spike is a functional simulator, so effects such as pipeline stalls and cache behavior are not captured.
- Results come from small isolated kernels, not full end-to-end Transformer inference.
- The latency of a new instruction is an assumption; the sensitivity sweep shows how much it matters.

## Links

- Foundation one-pager: _add link_
- Shared Drive: _add link_

## References

1. A. Vaswani et al., "Attention Is All You Need," arXiv:1706.03762, 2017.
2. D. Hendrycks and K. Gimpel, "Gaussian Error Linear Units (GELUs)," arXiv:1606.08415.
3. J. L. Ba, J. R. Kiros, and G. E. Hinton, "Layer Normalization," arXiv:1607.06450, 2016.
4. [The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA](https://docs.riscv.org/reference/isa/unpriv/rv32.html).
5. [Spike, the RISC-V ISA Simulator](https://github.com/riscv-software-src/riscv-isa-sim) (README: "Simulating a New Instruction").
6. [GNU assembler, RISC-V instruction formats (`.insn`)](https://www.sourceware.org/binutils/docs/as/RISC_002dV_002dFormats.html).
7. [Arm, "Exploring the Arm dot product instructions"](https://developer.arm.com/community/arm-community-blogs/b/tools-software-ides-blog/posts/exploring-the-arm-dot-product-instructions).
8. [WikiChip, AVX512 VNNI (`VPDPBUSD`)](https://en.wikichip.org/wiki/AVX512_VNNI).
9. [NVIDIA `dp4a`, as described in the MLIR NVVM dialect discussion](https://lists.llvm.org/pipermail/mlir-commits/2025-May/107793.html).
10. [RISC-V Vector Is Expanding (`Zvdot4a8i`)](https://fprox.substack.com/p/risc-v-vector-is-expanding).
11. [PySpike: Python bindings for Spike](https://pypi.org/project/spike/).

## Authors

Michelle Luu, Omar Elhanafy and Johnny Van — CECS 530, California State University, Long Beach.