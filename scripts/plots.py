
"""Make the report plots from results/*.csv and build/*_counts.csv.
Usage: python3 scripts/plots.py <name> <title> <custom_mnemonic>      e.g. bench_dot "DOT4" dot4
Colors: baseline = blue, custom = orange (validated palette, see the dataviz skill)."""
import csv
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE, CUST = "#2a78d6", "#eb6834"
MIX_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"
plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e4e3df", "grid.linewidth": 0.8, "font.size": 11, "axes.axisbelow": True})


def rows(path):
    return list(csv.DictReader(open(path)))


OUT_DIR = "results/plots"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/{name}.png", dpi=200)
    plt.close(fig)


def main():
    global OUT_DIR
    name, title, mnem = sys.argv[1:4]
    OUT_DIR = f"results/plots/{mnem}"
    os.makedirs(OUT_DIR, exist_ok=True)
    is_gelu = mnem == "gelu"
    all_results = rows(f"results/{name}_results.csv")
    prefix = "random_" if is_gelu else "rand_"
    res = [r for r in all_results if r["case"].startswith(prefix)]
    if not res:
        sys.exit(f"No random cases found for {title}")

    sizes = [int(r["n"]) for r in res]
    labels = [str(n) for n in sizes]
    positions = range(len(sizes))
    x_label = "Input value (signed Q8)" if is_gelu else "Vector length n (int8 elements)"

    # 1. Instruction counts (log scale: sizes span 64x)
    fig, ax = plt.subplots(figsize=(9, 4.5) if is_gelu else (7, 4.2))
    x = positions
    b = ax.bar([i - 0.2 for i in x], [int(r["base_instr"]) for r in res], 0.38, color=BASE, label="Baseline (software)")
    c = ax.bar([i + 0.2 for i in x], [int(r["custom_instr"]) for r in res], 0.38, color=CUST, label=f"With {title}")
    ax.bar_label(b, fontsize=9, padding=2); ax.bar_label(c, fontsize=9, padding=2)
    ax.set_yscale("log"); ax.set_xticks(list(x)); ax.set_xticklabels(labels, rotation=45 if is_gelu else 0)
    ax.set_xlabel(x_label); ax.set_ylabel("Instructions executed (log scale)")
    ax.set_title(f"{title}: instructions executed per kernel call", loc="left"); ax.legend(frameon=False)
    ax.set_ylim(top=ax.get_ylim()[1] * 1.6)
    save(fig, f"{name}_instructions")

    # 2. Speedup vs size
    fig, ax = plt.subplots(figsize=(9, 4.5) if is_gelu else (7, 4.2))
    plot_x = list(positions) if is_gelu else sizes
    ax.plot(plot_x, [float(r["instr_ratio"]) for r in res], "o-", color=BASE, lw=2, label="Instruction-count ratio")
    ax.plot(plot_x, [float(r["speedup"]) for r in res], "o-", color=CUST, lw=2, label="Modeled-cycle speedup")
    for i, (s, r) in enumerate(zip(plot_x, res)):
        ax.annotate(f'{float(r["speedup"]):.2f}x', (s, float(r["speedup"])), textcoords="offset points", xytext=(0, -16), ha="center", fontsize=9, color=MUTED)
        ax.annotate(f'{float(r["instr_ratio"]):.2f}x', (s, float(r["instr_ratio"])), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=MUTED)
    ax.axhline(1, color=MUTED, lw=1, ls=":")
    if is_gelu:
        ax.set_xticks(plot_x); ax.set_xticklabels(labels, rotation=45)
        ax.set_ylim(bottom=0)
    else:
        ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(labels)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.1)
    ax.set_xlabel(x_label if is_gelu else "Vector length n"); ax.set_ylabel("Baseline / custom (higher is better)")
    ax.set_title(f"{title}: speedup {'across test inputs' if is_gelu else 'vs input size'}", loc="left")
    ax.legend(frameon=False, loc="lower right" if not is_gelu else "best")
    save(fig, f"{name}_speedup")

    # 3. Sensitivity to the custom instruction's latency
    sens = rows(f"results/{name}_sensitivity.csv")
    lat = [int(r[f"{mnem}_latency_cycles"]) for r in sens]; sp = [float(r["speedup"]) for r in sens]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(lat, sp, "o-", color=CUST, lw=2, label=f"{title} modeled speedup")
    ax.axhline(1, color=MUTED, lw=1, ls=":"); ax.annotate("no speedup", (lat[-1], 1), xytext=(0, 6), textcoords="offset points", ha="right", fontsize=9, color=MUTED)
    for l, s in zip(lat, sp):
        ax.annotate(f"{s:.2f}x", (l, s), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=MUTED)
    ax.set_xlabel(f"Assumed {title} latency (cycles)"); ax.set_ylabel("Modeled speedup over baseline")
    largest = max(abs(n) for n in sizes) if is_gelu else max(sizes)
    ax.set_title(
        f"{title}: {'latency sensitivity' if is_gelu else 'sensitivity to the latency assumption'} "
        f"({'largest input magnitude' if is_gelu else 'n'} = {largest})", loc="left")
    ax.set_ylim(0, max(sp) * 1.2); ax.legend(frameon=False)
    save(fig, f"{name}_sensitivity")

    # 4. Instruction mix at the largest input magnitude / vector length
    counts = rows(f"build/{name}_counts.csv")
    big = max(range(len(res)), key=lambda i: abs(sizes[i]) if is_gelu else sizes[i])
    random_start = len(all_results) - len(res)
    base_row, cust_row = counts[2 * (random_start + big)], counts[2 * (random_start + big) + 1]
    groups = {"ALU": ["alu"], "Load/store": ["load", "store", "fp_load", "fp_store"],
              "Multiply/divide": ["mul", "div"],
              "FP arithmetic": ["fp_add", "fp_mul", "fp_fma", "fp_div", "fp_sqrt"], "FP other": ["fp_other"],
              "Branch/jump": ["branch", "branch_taken", "jump"], title: [mnem]}
    fig, ax = plt.subplots(figsize=(8, 3.8) if is_gelu else (7, 3.4))
    seen = set()
    for y, (lab, row) in enumerate([("With " + title, cust_row), ("Baseline", base_row)]):
        left = 0
        for color, (g, keys) in zip(MIX_COLORS, groups.items()):
            v = sum(int(row[k]) for k in keys)
            if v:
                ax.barh(y, v, left=left, color=color, edgecolor=SURFACE, linewidth=2, height=0.55, label=g if g not in seen else None)
                seen.add(g)
                if v > 0.05 * int(base_row['total']):
                    ax.text(left + v / 2, y, str(v), ha="center", va="center", color="white", fontsize=9, fontweight="bold")
            left += v
        ax.text(left + (5 if is_gelu else 80), y, f"{left}", va="center", fontsize=10)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["With " + title, "Baseline"]); ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Instructions executed ({x_label}: {sizes[big]})" if is_gelu else f"Instructions executed (n = {int(res[big]['n'])})")
    ax.set_title(f"{title}: instruction mix", loc="left")
    handles, labs = ax.get_legend_handles_labels()
    ax.legend(handles, labs, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.38), fontsize=9)
    ax.set_xlim(right=max(int(base_row['total']), int(cust_row['total'])) * 1.15)
    save(fig, f"{name}_mix")


if __name__ == "__main__":
    main()
