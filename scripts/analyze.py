"""Count executed instructions per kernel call from a Spike trace.

Usage: python3 scripts/analyze.py <name> <kernel_symbol> [<kernel_symbol> ...]
Reads build/<name>.log and build/<name>.elf, prints one CSV row per kernel call.
A "call" runs from the kernel's first instruction to its matching return, including helper functions it calls.
"""
import re
import subprocess
import sys
from collections import Counter

LINE = re.compile(r"core\s+\d+:\s+0x([0-9a-f]+)\s+\(0x[0-9a-f]+\)\s+(\S+)")

# Instruction classes used by the cost model. Spike prints some pseudo-instructions (mv, li, ret...).
CLASSES = {
    "alu": "add addi sub and andi or ori xor xori sll slli srl srli sra srai slt slti sltu sltiu "
           "lui auipc li mv nop not neg seqz snez sltz sgtz sext.b sext.h zext.b zext.h",
    "mul": "mul mulh mulhsu mulhu",
    "div": "div divu rem remu",
    "load": "lb lbu lh lhu lw",
    "store": "sb sh sw",
    "branch": "beq bne blt bge bltu bgeu beqz bnez blez bgez bltz bgtz bgt ble bgtu bleu",
    "jump": "jal jalr j jr ret call tail",
    "csr": "csrr csrw csrs csrc csrrw csrrs csrrc csrwi csrsi csrci",
    "fp_load": "flw", "fp_store": "fsw",
    "fp_add": "fadd.s fsub.s", "fp_mul": "fmul.s", "fp_fma": "fmadd.s fmsub.s fnmadd.s fnmsub.s",
    "fp_div": "fdiv.s", "fp_sqrt": "fsqrt.s",
    "fp_other": "fmv.s fneg.s fabs.s fsgnj.s fsgnjn.s fsgnjx.s fmin.s fmax.s feq.s flt.s fle.s "
                "fcvt.w.s fcvt.wu.s fcvt.s.w fcvt.s.wu fmv.x.w fmv.w.x fclass.s frcsr frflags",
    "dot4": "dot4", "gelu": "gelu",   # custom instructions, one class each
}
CLASS_OF = {m: c for c, ms in CLASSES.items() for m in ms.split()}
ORDER = list(CLASSES) + ["branch_taken"]   # branch_taken is split out of "branch" below


def symbols(elf, names):
    out = subprocess.run(["riscv64-unknown-elf-nm", "-S", elf], capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[3] in names:
            start = int(parts[0], 16)
            table[parts[3]] = (start, start + int(parts[1], 16))
    missing = set(names) - set(table)
    if missing:
        sys.exit(f"symbols not found in ELF: {missing}")
    return table


def kernel_calls(log, table):
    """Yield (kernel_name, Counter of classes) for each call, in execution order.
    A call starts when the kernel's first instruction runs and ends at its matching `ret`,
    so helper functions the kernel calls are counted too (jal/jalr go one level deeper,
    ret comes back up). A branch whose next instruction is not at pc+4 was taken; it is
    moved to "branch_taken"."""
    starts = {lo: name for name, (lo, hi) in table.items()}
    active, counts, depth, prev_branch_pc = None, None, 0, None
    for line in open(log):
        m = LINE.match(line)
        if not m:
            continue
        pc, mnem = int(m.group(1), 16), m.group(2)
        if active is None:
            if pc not in starts:
                continue
            active, counts, depth, prev_branch_pc = starts[pc], Counter(), 0, None
        if prev_branch_pc is not None and pc != prev_branch_pc + 4:
            counts["branch"] -= 1
            counts["branch_taken"] += 1
        prev_branch_pc = None
        if mnem not in CLASS_OF:
            sys.exit(f"unknown instruction '{mnem}' at {pc:#x}: add it to CLASSES")
        counts[CLASS_OF[mnem]] += 1
        if CLASS_OF[mnem] == "branch":
            prev_branch_pc = pc
        if mnem in ("jal", "jalr"):
            depth += 1
        elif mnem == "ret":
            if depth == 0:
                yield active, counts
                active = None
            else:
                depth -= 1


def main():
    name, kernels = sys.argv[1], sys.argv[2:]
    table = symbols(f"build/{name}.elf", set(kernels))
    print("call,kernel,total," + ",".join(ORDER))
    for i, (k, c) in enumerate(kernel_calls(f"build/{name}.log", table)):
        print(f"{i},{k},{sum(c.values())}," + ",".join(str(c.get(cl, 0)) for cl in ORDER))


if __name__ == "__main__":
    main()
