
#ifndef GELU_H
#define GELU_H

#include <stdint.h>

// GELU approximation using tanh:
// GELU(x) = 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))

// Fixed-point representation: signed 32-bit integers scaled by 256 (8 fractional bits).

// GELU using software fixed-point arithmetic.
int32_t gelu_baseline(int32_t x);

// Same result using the custom GELU instruction.
int32_t gelu_custom(int32_t x);


#endif
