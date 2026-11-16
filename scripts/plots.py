
"""Make report plots from results/*.csv and build/*_counts.csv.

Usage:
  python3 scripts/plots.py <name> <title> <custom_mnemonic>
"""

import csv
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE, CUST = "#2a78d6", "#eb6834"
MIX_COLORS = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#6250d6"
]
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e4e3df",
    "grid.linewidth": 0.8,
    "font.size": 11,
    "axes.axisbelow": True
})


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


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

    values = [int(r["n"]) for r in res]
    labels = [str(v) for v in values]
    positions = list(range(len(res)))

    # GELU uses signed Q8 inputs; DOT4 uses vector lengths.
    x_label = "Input value (signed Q8)" if is_gelu else "Vector length n (int8 elements)"

    # 1. Instruction counts
    fig, ax = plt.subplots(figsize=(9, 4.5))

    b = ax.bar(
        [i - 0.2 for i in positions],
        [int(r["base_instr"]) for r in res],
        0.38, color=BASE, label="Baseline (software)"
    )
    c = ax.bar(
        [i + 0.2 for i in positions],
        [int(r["custom_instr"]) for r in res],
        0.38, color=CUST, label=f"With {title}"
    )

    ax.bar_label(b, fontsize=8, padding=2)
    ax.bar_label(c, fontsize=8, padding=2)
    ax.set_yscale("log")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45 if is_gelu else 0)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Instructions executed (log scale)")
    ax.set_title(f"{title}: instructions executed per kernel call", loc="left")
    ax.legend(frameon=False)
    ax.set_ylim(bottom=1, top=ax.get_ylim()[1] * 1.6)
    save(fig, f"{name}_instructions")

    # 2. Speedup
    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.plot(
        positions, [float(r["instr_ratio"]) for r in res],
        "o-", color=BASE, lw=2, label="Instruction-count ratio"
    )
    ax.plot(
        positions, [float(r["speedup"]) for r in res],
        "o-", color=CUST, lw=2, label="Modeled-cycle speedup"
    )

    for i, r in enumerate(res):
        ax.annotate(
            f'{float(r["speedup"]):.2f}x',
            (i, float(r["speedup"])),
            textcoords="offset points", xytext=(0, -16),
            ha="center", fontsize=8, color=MUTED
        )
        ax.annotate(
            f'{float(r["instr_ratio"]):.2f}x',
            (i, float(r["instr_ratio"])),
            textcoords="offset points", xytext=(0, 8),
            ha="center", fontsize=8, color=MUTED
        )

    ax.axhline(1, color=MUTED, lw=1, ls=":")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45 if is_gelu else 0)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Baseline / custom (higher is better)")
    ax.set_title(f"{title}: speedup across test inputs", loc="left")
    ax.legend(frameon=False)

    if is_gelu:
        ax.set_ylim(bottom=0)
    else:
        ax.set_ylim(0, ax.get_ylim()[1] * 1.1)

    save(fig, f"{name}_speedup")

    # 3. Sensitivity to custom instruction latency
    sens = rows(f"results/{name}_sensitivity.csv")
    lat = [int(r[f"{mnem}_latency_cycles"]) for r in sens]
    sp = [float(r["speedup"]) for r in sens]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(lat, sp, "o-", color=CUST, lw=2, label=f"{title} modeled speedup")
    ax.axhline(1, color=MUTED, lw=1, ls=":")
    ax.annotate(
        "no speedup", (lat[-1], 1),
        xytext=(0, 6), textcoords="offset points",
        ha="right", fontsize=9, color=MUTED
    )

    for l, s in zip(lat, sp):
        ax.annotate(
            f"{s:.2f}x", (l, s),
            textcoords="offset points", xytext=(0, 8),
            ha="center", fontsize=9, color=MUTED
        )

    largest = max(abs(v) for v in values) if is_gelu else max(values)
    ax.set_xlabel(f"Assumed {title} latency (cycles)")
    ax.set_ylabel("Modeled speedup over baseline")
    ax.set_title(
        f"{title}: latency sensitivity "
        f"(largest {'input magnitude' if is_gelu else 'vector size'} = {largest})",
        loc="left"
    )
    ax.set_ylim(bottom=0, top=max(sp) * 1.2)
    ax.legend(frameon=False)
    save(fig, f"{name}_sensitivity")

    # 4. Instruction mix at the largest input magnitude / vector length
    counts = rows(f"build/{name}_counts.csv")

    big = max(
        range(len(res)),
        key=lambda i: abs(values[i]) if is_gelu else values[i]
    )

    random_start = len(all_results) - len(res)

    base_row = counts[2 * (random_start + big)]
    cust_row = counts[2 * (random_start + big) + 1]

    groups = {
        "ALU": ["alu"],
        "Load/store": ["load", "store", "fp_load", "fp_store"],
        "Multiply/divide": ["mul", "div"],
        "FP arithmetic": ["fp_add", "fp_mul", "fp_fma", "fp_div", "fp_sqrt"],
        "FP other": ["fp_other"],
        "Branch/jump": ["branch", "branch_taken", "jump"],
        title: [mnem]
    }

    fig, ax = plt.subplots(figsize=(8, 3.8))
    seen = set()

    for y, (lab, row) in enumerate([
        ("With " + title, cust_row),
        ("Baseline", base_row)
    ]):
        left = 0

        for color, (group, keys) in zip(MIX_COLORS, groups.items()):
            v = sum(int(row[k]) for k in keys)

            if v:
                ax.barh(
                    y, v, left=left, color=color,
                    edgecolor=SURFACE, linewidth=2,
                    height=0.55,
                    label=group if group not in seen else None
                )
                seen.add(group)

                if v > 0.05 * int(base_row["total"]):
                    ax.text(
                        left + v / 2, y, str(v),
                        ha="center", va="center",
                        color="white", fontsize=9, fontweight="bold"
                    )

            left += v

        ax.text(left + 5, y, str(left), va="center", fontsize=10)

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["With " + title, "Baseline"])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Instructions executed ({x_label}: {values[big]})")
    ax.set_title(f"{title}: instruction mix", loc="left")

    handles, labs = ax.get_legend_handles_labels()
    ax.legend(
        handles, labs, frameon=False, ncol=3,
        loc="upper center", bbox_to_anchor=(0.5, -0.38),
        fontsize=9
    )

    ax.set_xlim(right=max(
        int(base_row["total"]), int(cust_row["total"])
    ) * 1.15)

    save(fig, f"{name}_mix")


if __name__ == "__main__":
    main()
