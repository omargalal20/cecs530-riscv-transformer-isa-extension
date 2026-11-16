#include "gelu.h"

// Custom GELU implementation.
//
// Input/output: signed Q8.
// The custom instruction takes one Q8 input and returns one Q8 result.
//
// Encoding:
// custom-0 opcode, funct3=1, funct7=0, rs2=x0.

__attribute__((noinline))
int32_t gelu_custom(int32_t x_q8)
{
    int32_t result;

    __asm__ volatile(
        ".insn r 0x0B, 1, 0, %0, %1, x0"
        : "=r"(result)
        : "r"(x_q8)
    );

    return result;
}
