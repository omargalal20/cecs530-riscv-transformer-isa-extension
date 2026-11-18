# Directed test for GELU (RV32).
# a0 = 0 means pass; a0 = test number means failure.

    .section .text
    .globl main

.macro CHECK_GELU input, expected, fail
    li      a0, \fail
    li      t0, \input
    .insn   r 0x0B, 1, 0, t1, t0, x0
    li      t2, \expected
    bne     t1, t2, done
.endm

main:
    # Negative inputs
    CHECK_GELU -1536, 0,    1
    CHECK_GELU -1024, 0,    2
    CHECK_GELU -768,  -1,   3
    CHECK_GELU -512,  -12,  4
    CHECK_GELU -256,  -41,  5
    CHECK_GELU -128,  -40,  6
    CHECK_GELU -1,    0,    7

    # Zero
    CHECK_GELU 0,     0,    8

    # Positive inputs
    CHECK_GELU 1,     1,    9
    CHECK_GELU 128,   88,   10
    CHECK_GELU 256,   215,  11
    CHECK_GELU 512,   500,  12
    CHECK_GELU 768,   767,  13
    CHECK_GELU 1023,  1023, 14
    CHECK_GELU 1024,  1024, 15
    CHECK_GELU 1536,  1536, 16

    li      a0, 0

done:
    ret
