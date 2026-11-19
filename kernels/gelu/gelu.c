#include "gelu.h"
#include "gelu_lut.h" // the generated 65-entry Q15 table 
#include <stdint.h>

// Returns value divided by 2^shift, rounded to nearest, ties away from zero
static inline __attribute__((always_inline))
int64_t round_shift(int64_t value, int shift) {
    int64_t half = (int64_t) 1 << (shift - 1);
    if (value >= 0) {
        return (value + half) >> shift;
    } else {
        return -(((-value) + half) >> shift);
    }
}

// Input: signed 32-bit integer stored in Q8 fixed-point format
__attribute__((noinline))
int32_t gelu_baseline(int32_t x) {
    // Q8 uses a scale factor of 256, so 1024 / 256 = 4.0 and -1024 / 256 = -4.0
    if (x >= 1024) 
        return x; // as x >= 4, tanh(z) approaches 1, GELU(x) ≈ x
    
    if (x <= -1024)
        return 0; // as x <= -4, tanh(z) approaches -1, so GELU(x) ≈ 0

    // Convert x from Q8 to Q24 (2^24 / 2^8 = 2^16)
    int64_t x_q24 = (int64_t) x * 65536;
    
    // Gelu calculations
    int64_t x_squared = round_shift(x_q24 * x_q24, 24);
    int64_t x_cubed = round_shift(x_squared * x_q24, 24);
    int64_t scaled_x_cubed = round_shift(750193 * x_cubed, 24); // 0.044715 * x^3, 0.044715 = 750193 in Q24
    int64_t tanh_input = x_q24 + scaled_x_cubed; // x + 0.044715 * x^3
    int64_t new_tanh = round_shift(13386282 * tanh_input, 24); //  0.7978845608 * (x + 0.044715 * x^3),  0.7978845608 = 13386282 in Q24

    // Look up tanh
    int64_t abs_tanh;
    if (new_tanh < 0) {
        abs_tanh = -new_tanh;
    } else {
        abs_tanh = new_tanh;
    }

    // Each LUT interval is 1/16 which equals 2^20 in Q24
    int64_t lut_index = abs_tanh >> 20;
    int64_t lut_remainder = abs_tanh & ((1 << 20) - 1); // - 1 to get the 20 lower bits

    int32_t tanh_value;
    if (lut_index >= 64) {
        tanh_value = gelu_tanh_lut_q15[64];
    } else {
        int32_t lower_value = gelu_tanh_lut_q15[lut_index];
        int32_t upper_value = gelu_tanh_lut_q15[lut_index + 1];
        // Interpolate between two LUT values based on how far input falls between them
        tanh_value = lower_value + (int32_t) round_shift((int64_t)(upper_value - lower_value) * lut_remainder, 20);
    }

    if (new_tanh < 0)
        tanh_value = -tanh_value;

    return (int32_t) round_shift((int64_t) x * (32768 + tanh_value), 16); // 0.5 * x * result from tanh, 0.5 = 32768 in Q24
}

#ifdef __riscv
__attribute__((noinline))
int32_t gelu_custom(int32_t x) {
    int32_t result;
    __asm__ volatile (
        ".insn r 0x0b, 1, 0, %0, %1, x0"
        : "=r"(result) : "r"(x));
    return result;
}
#endif
