
#include "gelu.h"
#include "gelu_lut.h"

// Round a signed integer division by 2^shift to nearest,
// with ties away from zero.
//
// All values passed to this helper are bounded well within int64_t.
static int64_t round_shift_away(int64_t value, unsigned int shift)
{
    int64_t half = 1LL << (shift - 1);

    if (value >= 0)
        return (value + half) >> shift;

    return -(((-value) + half) >> shift);
}

// Approximate tanh(z), where z is represented in Q24.
// Returns a signed Q15 result.
static int32_t gelu_tanh_q15(int64_t z_q24)
{
    const int64_t step = 1LL << 20;  // 1/16 in Q24
    const int64_t limit = 4LL << 24;

    int sign = (z_q24 < 0) ? -1 : 1;
    int64_t magnitude = (z_q24 < 0) ? -z_q24 : z_q24;

    // Clamp to the final LUT entry outside [-4, 4].
    if (magnitude >= limit)
        return sign * gelu_tanh_lut_q15[64];

    // Determine the LUT interval and interpolation fraction.
    unsigned int index = (unsigned int)(magnitude >> 20);
    int64_t remainder = magnitude & (step - 1);

    int32_t lower = gelu_tanh_lut_q15[index];
    int32_t upper = gelu_tanh_lut_q15[index + 1];

    int64_t delta = (int64_t)(upper - lower) * remainder;

    int64_t interpolated =
        (int64_t)lower + round_shift_away(delta, 20);

    return sign * (int32_t)interpolated;
}

// Software GELU implementation.
//
// Input/output: signed Q8
// Polynomial intermediate: signed Q24
// Tanh LUT output: signed Q15
__attribute__((noinline))
int32_t gelu_baseline(int32_t x_q8)
{
    // At and beyond these boundaries, the Q8 GELU result
    // rounds to x for positive inputs and zero for negative inputs.
    if (x_q8 >= 1024)
        return x_q8;

    if (x_q8 <= -1024)
        return 0;

    // Convert Q8 input to Q24.
    int64_t x_q24 = (int64_t)x_q8 * 65536;

    // Calculate x^2 and x^3 in Q24.
    int64_t x2_q24 =
        round_shift_away(x_q24 * x_q24, 24);

    int64_t x3_q24 =
        round_shift_away(x2_q24 * x_q24, 24);

    // Q24 representation of 0.044715.
    const int64_t coeff_0044715_q24 = 750193;

    // Q24 representation of sqrt(2/pi).
    const int64_t coeff_sqrt_2_over_pi_q24 = 13386282;

    // Calculate x + 0.044715 * x^3.
    int64_t cubic_term_q24 =
        round_shift_away(coeff_0044715_q24 * x3_q24, 24);

    int64_t inner_q24 = x_q24 + cubic_term_q24;

    // Calculate sqrt(2/pi) * (x + 0.044715 * x^3).
    int64_t z_q24 =
        round_shift_away(coeff_sqrt_2_over_pi_q24 * inner_q24, 24);

    // Approximate tanh(z) in Q15.
    int32_t tanh_q15 = gelu_tanh_q15(z_q24);

    // GELU(x) = x * (1 + tanh(z)) / 2.
    //
    // (32768 + tanh_q15) represents (1 + tanh(z)) in Q15.
    int64_t numerator =
        (int64_t)x_q8 * (32768 + tanh_q15);

    // Convert the result back to Q8.
    return (int32_t)round_shift_away(numerator, 16);
}
