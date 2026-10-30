/* Linker script for bare-metal programs on Spike (its RAM starts at 0x80000000). */
OUTPUT_ARCH("riscv")
ENTRY(_start)

SECTIONS
{
  . = 0x80000000;
  .text.init : { *(.text.init) }

  . = ALIGN(0x1000);
  .tohost : { *(.tohost) }

  . = ALIGN(0x1000);
  .text : { *(.text .text.*) }

  . = ALIGN(0x1000);
  .data : { *(.data .data.*) *(.sdata .sdata.*) *(.rodata .rodata.*) *(.srodata .srodata.*) }

  .bss : { *(.bss .bss.*) *(.sbss .sbss.*) *(COMMON) }

  . = ALIGN(16);
  . += 0x4000;          /* reserve 16 KiB for the stack */
  _stack_top = .;
  _end = .;
}
