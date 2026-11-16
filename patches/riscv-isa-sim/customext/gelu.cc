
#include "insn_macros.h"
#include "extension.h"
#include "decode_macros.h"
#include "gelu_lut.h"

#include <cstdint>

// Assembly register names.
// Use unique names to avoid collisions with dot4.cc.
struct : public arg_t {
    std::string to_string(insn_t insn) const override {
        return xpr_name[insn.rd()];
    }
} gelu_xrd;

struct : public arg_t {
    std::string to_string(insn_t insn) const override {
        return xpr_name[insn.rs1()];
    }
} gelu_xrs1;


// Round to nearest, with ties away from zero.
static int64_t gelu_round_shift(int64_t value, unsigned int shift)
{
    const int64_t half = 1LL << (shift - 1);

    if (value >= 0)
        return (value + half) >> shift;

    return -(((-value) + half) >> shift);
}


// Calculate tanh(z), where z is Q24.
// Return value is signed Q15.
static int32_t gelu_tanh_q15(int64_t z_q24)
{
    const int64_t limit = 4LL << 24;
    const int64_t step = 1LL << 20;

    const int sign = (z_q24 < 0) ? -1 : 1;
    const int64_t magnitude = (z_q24 < 0) ? -z_q24 : z_q24;

    if (magnitude >= limit)
        return sign * gelu_tanh_lut_q15[64];

    const unsigned int index =
        static_cast<unsigned int>(magnitude >> 20);

    const int64_t remainder = magnitude & (step - 1);

    const int32_t lower = gelu_tanh_lut_q15[index];
    const int32_t upper = gelu_tanh_lut_q15[index + 1];

    const int64_t delta =
        static_cast<int64_t>(upper - lower) * remainder;

    const int64_t interpolated =
        lower + gelu_round_shift(delta, 20);

    return sign * static_cast<int32_t>(interpolated);
}


// GELU calculation.
//
// Input:  signed Q8
// Output: signed Q8
// Intermediate polynomial: Q24
// Tanh lookup table: Q15
static int32_t gelu_compute(int32_t x_q8)
{
    // GELU tails at Q8 precision.
    if (x_q8 >= 1024)
        return x_q8;

    if (x_q8 <= -1024)
        return 0;

    // Convert Q8 input to Q24.
    const int64_t x_q24 =
        static_cast<int64_t>(x_q8) * 65536;

    // Calculate x^2 and x^3 in Q24.
    const int64_t x2_q24 =
        gelu_round_shift(x_q24 * x_q24, 24);

    const int64_t x3_q24 =
        gelu_round_shift(x2_q24 * x_q24, 24);

    // Q24 coefficients.
    const int64_t coeff_0044715_q24 = 750193;
    const int64_t coeff_sqrt_2_over_pi_q24 = 13386282;

    // 0.044715 * x^3
    const int64_t cubic_term_q24 =
        gelu_round_shift(coeff_0044715_q24 * x3_q24, 24);

    // x + 0.044715 * x^3
    const int64_t inner_q24 = x_q24 + cubic_term_q24;

    // sqrt(2/pi) * (x + 0.044715 * x^3)
    const int64_t z_q24 =
        gelu_round_shift(
            coeff_sqrt_2_over_pi_q24 * inner_q24, 24);

    // tanh(z) in Q15.
    const int32_t tanh_q15 = gelu_tanh_q15(z_q24);

    // GELU(x) = x * (1 + tanh(z)) / 2.
    const int64_t numerator =
        static_cast<int64_t>(x_q8) * (32768 + tanh_q15);

    return static_cast<int32_t>(
        gelu_round_shift(numerator, 16));
}


// GELU instruction execution.
static reg_t gelu(processor_t* p, insn_t insn, reg_t pc)
{
    const int32_t input =
        static_cast<int32_t>(p->get_state()->XPR[insn.rs1()]);

    const int32_t result = gelu_compute(input);

    p->get_state()->XPR.write(
        insn.rd(),
        static_cast<reg_t>(static_cast<int64_t>(result)));

    return pc + 4;
}


// GELU extension.
class gelu_t : public extension_t
{
public:
    const char* name() const override {
        return "gelu";
    }

    std::vector<insn_desc_t> get_instructions(
        const processor_t &) override
    {
        return {
            {
                0x0000100B,
                0xFFF0707F,
                gelu, gelu, gelu, gelu,
                gelu, gelu, gelu, gelu
            }
        };
    }

    std::vector<disasm_insn_t*> get_disasms(
        const processor_t *) override
    {
        return {
            new disasm_insn_t(
                "gelu",
                0x0000100B,
                0xFFF0707F,
                {&gelu_xrd, &gelu_xrs1}
            )
        };
    }
};


// Register extension.
REGISTER_EXTENSION(gelu, []() {
    static gelu_t ext;
    return &ext;
})
