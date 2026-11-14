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
    return [m.group(1) for line in open(out_path) if (m := re.match(r"(\S+) n=(\d+)", line))], \
           [int(m.group(2)) for line in open(out_path) if (m := re.match(r"(\S+) n=(\d+)", line))]


def paired(rows, base_k, cust_k):
    """Calls come in (baseline, custom) pairs, in the order the program ran them."""
    for i in range(0, len(rows), 2):
        b, c = rows[i], rows[i + 1]
        assert b["kernel"] == base_k and c["kernel"] == cust_k, "unexpected call order"
        yield b, c


def main():
    name, base_k, cust_k, mnem = sys.argv[1:5]
    rows = read_counts(f"build/{name}_counts.csv")
    names, sizes = case_names(f"build/{name}.out")
    out = open(f"results/{name}_results.csv", "w", newline="")
    w = csv.writer(out)
    w.writerow(["case", "n", "base_instr", "custom_instr", "instr_ratio",
                "base_cycles", "custom_cycles", "speedup"])
    for (b, c), case, n in zip(paired(rows, base_k, cust_k), names, sizes):
        bi, ci = int(b["total"]), int(c["total"])
        bc, cc = cycles(b), cycles(c)
        w.writerow([case, n, bi, ci, round(bi / ci, 3), bc, cc, round(bc / cc, 3)])
    out.close()
    # Sensitivity: sweep the custom instruction's latency on the largest random case
    big = [p for p, nm in zip(paired(rows, base_k, cust_k), names) if nm.startswith("rand_1024")][0]
    with open(f"results/{name}_sensitivity.csv", "w", newline="") as f:
        sw = csv.writer(f)
        sw.writerow([f"{mnem}_latency_cycles", "speedup"])
        for lat in range(1, 9):
            sw.writerow([lat, round(cycles(big[0]) / cycles(big[1], {mnem: lat}), 3)])


if __name__ == "__main__":
    main()
