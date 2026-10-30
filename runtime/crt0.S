# Minimal bare-metal startup for Spike (RV32).
# Sets up the stack, calls main(), then reports main's return value to Spike
# through the HTIF "tohost" word.

    .section .text.init
    .globl _start
_start:
    la      sp, _stack_top      # point the stack pointer at the stack we reserve in link.ld
    call    main                # run the C program; its return value lands in a0
    slli    a0, a0, 1           # a0 = a0 << 1
    ori     a0, a0, 1           # a0 = (code << 1) | 1  -> "exit request"
    la      t0, tohost
    sw      a0, 0(t0)           # low half of tohost: the exit request
    sw      zero, 4(t0)         # high half of tohost: 0 (tohost is 64 bits wide)
1:  j       1b                  # wait here until Spike stops the simulation

    .section .tohost, "aw", @progbits
    .align  6
    .globl  tohost
tohost:     .dword 0
    .globl  fromhost
fromhost:   .dword 0
