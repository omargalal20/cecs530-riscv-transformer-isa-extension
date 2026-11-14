# Directed test for DOT4 (RV32). Exit code 0 = pass, 1 = first DOT4 wrong, 2 = second wrong.
# Ported from Johnny's dot4_test.S: sd (RV64 only) replaced by exit through crt0.
    .section .text
    .globl main
main:
    li      t0, 0x7F807F80      # A = [-128, 127, -128, 127]
    li      t1, 0x807F807F      # B = [127, -128, 127, -128]
    li      t2, 0               # accumulator
    .insn r 0x0B, 0, 0, t2, t0, t1
    li      t3, -65024          # 4 * (-128 * 127)
    li      a0, 1
    bne     t2, t3, done
    .insn r 0x0B, 0, 0, t2, t0, t1
    li      t3, -130048         # accumulates on top of the first result
    li      a0, 2
    bne     t2, t3, done
    li      a0, 0
done:
    ret
