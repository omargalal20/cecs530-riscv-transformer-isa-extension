
#ifndef GELU_H
#define GELU_H

#include <stdint.h>

// GELU input and output use signed Q8 fixed-point format.
// A real value is represented as value * 256.
//
// Example:
//   1.0  = 256
//  -1.0  = -256
//
// Returns the GELU result in the same Q8 format.

// Software GELU implementation.
int32_t gelu_baseline(int32_t x_q8);

// Custom-instruction GELU implementation.
int32_t gelu_custom(int32_t x_q8);

#endif
