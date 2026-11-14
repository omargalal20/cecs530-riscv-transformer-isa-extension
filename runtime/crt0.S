# Startup code: set the stack, turn on the FP unit, call main, report main's return value
# through the HTIF "tohost" word. Spike exits with that value as its exit status.
    .section .text.init
    .globl _start
_start:
    la      sp, _stack_top
    # Spike boots with the FP unit off (mstatus.FS = 0); set FS = 01 so FP instructions work
    li      t0, 0x2000
    csrs    mstatus, t0
    call    main
    slli    a0, a0, 1
    ori     a0, a0, 1
    la      t0, tohost
    sw      a0, 0(t0)
    sw      zero, 4(t0)
1:  j       1b

    .section .tohost, "aw", @progbits
    .align  6
    .globl  tohost
tohost:     .dword 0
    .globl  fromhost
fromhost:   .dword 0
