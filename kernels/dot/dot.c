#include "dot.h"

// noinline keeps each kernel as its own function, so the analysis script can
// count the instructions executed inside it.

__attribute__((noinline))
int32_t dot_baseline(const int8_t *a, const int8_t *b, int n)
{
    int32_t acc = 0;
    for (int i = 0; i < n; i++)
        acc += (int32_t)a[i] * (int32_t)b[i];
    return acc;
}

typedef uint32_t __attribute__((may_alias)) word_t;

__attribute__((noinline))
int32_t dot_custom(const int8_t *a, const int8_t *b, int n)
{
    int32_t acc = 0;
    const word_t *pa = (const word_t *)a;
    const word_t *pb = (const word_t *)b;
    for (int i = 0; i < n / 4; i++) {
        uint32_t x = pa[i];   // four int8 values packed in one 32-bit word
        uint32_t y = pb[i];
        // DOT4: acc = acc + x.b0*y.b0 + x.b1*y.b1 + x.b2*y.b2 + x.b3*y.b3
        __asm__ volatile(".insn r 0x0B, 0, 0, %0, %1, %2"
                         : "+r"(acc) : "r"(x), "r"(y));
    }
    return acc;
}
