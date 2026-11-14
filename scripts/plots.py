"""Make the report plots from results/*.csv and build/*_counts.csv.
Usage: python3 scripts/plots.py <name> <title> <custom_mnemonic>      e.g. bench_dot "DOT4" dot4
Colors: baseline = blue, custom = orange (validated palette, see the dataviz skill)."""
import csv
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


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"results/plots/{name}.png", dpi=200)
    plt.close(fig)


def main():
    name, title, mnem = sys.argv[1:4]
    res = [r for r in rows(f"results/{name}_results.csv") if r["case"].startswith("rand_")]
    sizes = [int(r["n"]) for r in res]
    labels = [str(n) for n in sizes]

    # 1. Instruction counts (log scale: sizes span 64x)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = range(len(sizes))
    b = ax.bar([i - 0.2 for i in x], [int(r["base_instr"]) for r in res], 0.38, color=BASE, label="Baseline (software)")
    c = ax.bar([i + 0.2 for i in x], [int(r["custom_instr"]) for r in res], 0.38, color=CUST, label=f"With {title}")
    ax.bar_label(b, fontsize=9, padding=2); ax.bar_label(c, fontsize=9, padding=2)
    ax.set_yscale("log"); ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_xlabel("Vector length n (int8 elements)"); ax.set_ylabel("Instructions executed (log scale)")
    ax.set_title(f"{title}: instructions executed per kernel call", loc="left"); ax.legend(frameon=False)
    ax.set_ylim(top=ax.get_ylim()[1] * 1.6)
    save(fig, f"{name}_instructions")

    # 2. Speedup vs size
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(sizes, [float(r["instr_ratio"]) for r in res], "o-", color=BASE, lw=2, label="Instruction-count ratio")
    ax.plot(sizes, [float(r["speedup"]) for r in res], "o-", color=CUST, lw=2, label="Modeled-cycle speedup")
    for s, r in zip(sizes, res):
        ax.annotate(f'{float(r["speedup"]):.2f}x', (s, float(r["speedup"])), textcoords="offset points", xytext=(0, -16), ha="center", fontsize=9, color=MUTED)
        ax.annotate(f'{float(r["instr_ratio"]):.2f}x', (s, float(r["instr_ratio"])), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=MUTED)
    ax.axhline(1, color=MUTED, lw=1, ls=":")
    ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(labels)
    ax.set_xlabel("Vector length n"); ax.set_ylabel("Baseline / custom (higher is better)")
    ax.set_title(f"{title}: speedup vs input size", loc="left"); ax.legend(frameon=False, loc="lower right")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.1)
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
    ax.set_title(f"{title}: sensitivity to the latency assumption (n = {max(sizes)})", loc="left")
    ax.set_ylim(0, max(sp) * 1.2); ax.legend(frameon=False)
    save(fig, f"{name}_sensitivity")

    # 4. Instruction mix at the largest size
    counts = rows(f"build/{name}_counts.csv")
    big = max(range(len(res)), key=lambda i: int(res[i]["n"]))
    base_row, cust_row = counts[2 * big], counts[2 * big + 1]
    groups = {"ALU": ["alu"], "Load/store": ["load", "store", "fp_load", "fp_store"],
              "Multiply/divide": ["mul", "div"],
              "FP arithmetic": ["fp_add", "fp_mul", "fp_fma", "fp_div", "fp_sqrt"], "FP other": ["fp_other"],
              "Branch/jump": ["branch", "branch_taken", "jump"], title: [mnem]}
    fig, ax = plt.subplots(figsize=(7, 3.4))
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
        ax.text(left + 80, y, f"{left}", va="center", fontsize=10)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["With " + title, "Baseline"]); ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Instructions executed (n = {int(res[big]['n'])})"); ax.set_title(f"{title}: instruction mix", loc="left")
    handles, labs = ax.get_legend_handles_labels()
    ax.legend(handles, labs, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.38), fontsize=9)
    ax.set_xlim(right=max(int(base_row['total']), int(cust_row['total'])) * 1.15)
    save(fig, f"{name}_mix")


if __name__ == "__main__":
    main()
