
"""Cost model: turn instruction counts into modeled cycles.

modeled_cycles = sum over classes of (instruction count x cycles per instruction)
The same table is applied to baseline and custom code, so the comparison is fair.

Usage: python3 scripts/model.py <name> <baseline_kernel> <custom_kernel> <custom_mnemonic>
Reads build/<name>.out (case names), build/<name>_counts.csv; writes results/<name>_results.csv
"""
import csv
import json
import re
import sys

LAT = json.load(open("model/latencies.json"))["cycles"]

# Latencies tried for the custom instruction. GELU is a bigger unit than DOT4, so it gets a wider sweep.
SWEEPS = {"dot4": range(1, 9), "gelu": [1, 2, 4, 8, 16, 24, 32, 48, 64]}


def class_of_custom(mnemonic):
    return mnemonic          # the class name of a custom instruction equals its mnemonic


def cycles(row, overrides=None):
    lat = dict(LAT, **(overrides or {}))
    total = 0
    for k, v in row.items():
        if k in ("call", "kernel", "total") or not int(v):
            continue
        if k not in lat:
            sys.exit(f"no latency for instruction class '{k}' in model/latencies.json")
        total += int(v) * lat[k]
    return total


def read_counts(path):
    return list(csv.DictReader(open(path)))


def case_names(out_path):
    names, sizes = [], []
    pattern = re.compile(r"(\S+)\s+(?:n|input)=(-?\d+)")
    for line in open(out_path):
        match = pattern.match(line)
        if match:
            names.append(match.group(1))
            sizes.append(int(match.group(2)))
    return names, sizes


def paired(rows, base_k, cust_k):
    """Calls come in (baseline, custom) pairs, in the order the program ran them."""
    if len(rows) % 2:
        sys.exit("instruction-count rows are not in complete pairs")
    for i in range(0, len(rows), 2):
        b, c = rows[i], rows[i + 1]
        if b["kernel"] != base_k or c["kernel"] != cust_k:
            sys.exit(f"unexpected call order at rows {i} and {i + 1}")
        yield b, c


def main():
    name, base_k, cust_k, mnem = sys.argv[1:5]
    rows = read_counts(f"build/{name}_counts.csv")
    names, sizes = case_names(f"build/{name}.out")
    pairs = list(paired(rows, base_k, cust_k))

    if len(pairs) != len(names):
        sys.exit(f"case/count mismatch: {len(names)} benchmark cases, {len(pairs)} instruction-count pairs")

    with open(f"results/{name}_results.csv", "w", newline="") as out:
        w = csv.writer(out, lineterminator="\n")
        w.writerow(["case", "n", "base_instr", "custom_instr", "instr_ratio",
                    "base_cycles", "custom_cycles", "speedup"])
        for (b, c), case, n in zip(pairs, names, sizes):
            bi, ci = int(b["total"]), int(c["total"])
            bc, cc = cycles(b), cycles(c)
            w.writerow([case, n, bi, ci, round(bi / ci, 3), bc, cc, round(bc / cc, 3)])

    # Sensitivity: sweep the custom instruction's latency on the largest random case.
    random_cases = [(n, pair) for pair, nm, n in zip(pairs, names, sizes)
                    if nm.startswith(("rand_", "random_"))]
    if not random_cases:
        sys.exit("no random cases found for sensitivity analysis")

    big = max(random_cases, key=lambda c: abs(c[0]) if mnem == "gelu" else c[0])[1]

    with open(f"results/{name}_sensitivity.csv", "w", newline="") as f:
        sw = csv.writer(f, lineterminator="\n")
        sw.writerow([f"{mnem}_latency_cycles", "speedup"])
        for lat in SWEEPS.get(mnem, range(1, 9)):
            sw.writerow([lat, round(cycles(big[0]) / cycles(big[1], {mnem: lat}), 3)])


if __name__ == "__main__":
    main()
