.section .text
.globl _start

_start:
    # A = [-128, 127, -128, 127]
    li t0, 0x7F807F80

    # B = [127, -128, 127, -128]
    li t1, 0x807F807F

    # Initial accumulator = 0
    li t2, 0

    # First DOT4: expected -65024
    .insn r 0x0b, 0, 0, t2, t0, t1

    li t3, -65024
    bne t2, t3, fail

    # Second DOT4: expected -130048
    .insn r 0x0b, 0, 0, t2, t0, t1

    li t3, -130048
    bne t2, t3, fail

pass:
    li t4, 1
    j finish

fail:
    li t4, 3

finish:
    la t5, tohost
    sd t4, 0(t5)

1:
    j 1b

.section .tohost,"aw",@progbits
.align 3
.globl tohost
tohost:
    .dword 0

.globl fromhost
fromhost:
    .dword 0
