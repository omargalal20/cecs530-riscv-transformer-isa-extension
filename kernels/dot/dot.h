#ifndef DOT_H
#define DOT_H
#include <stdint.h>

// int8 dot product: sum of a[i] * b[i], accumulated in int32.
int32_t dot_baseline(const int8_t *a, const int8_t *b, int n);

// Same result using the custom DOT4 instruction. n must be a multiple of 4,
// and a and b must be 4-byte aligned.
int32_t dot_custom(const int8_t *a, const int8_t *b, int n);
#endif
