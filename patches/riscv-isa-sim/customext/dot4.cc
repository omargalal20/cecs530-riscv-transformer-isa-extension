#include "insn_macros.h"
#include "extension.h"
#include "decode_macros.h"
#include <cstdint>

// Assembly register names
struct : public arg_t {
    std::string to_string(insn_t insn) const override {
        return xpr_name[insn.rd()];
    }
} xrd;

struct : public arg_t {
    std::string to_string(insn_t insn) const override {
        return xpr_name[insn.rs1()];
    }
} xrs1;

struct : public arg_t {
    std::string to_string(insn_t insn) const override {
        return xpr_name[insn.rs2()];
    }
} xrs2;


// DOT4 execution
static reg_t dot4(processor_t* p, insn_t insn, reg_t pc)
{
    reg_t a = p->get_state()->XPR[insn.rs1()];
    reg_t b = p->get_state()->XPR[insn.rs2()];
    reg_t acc = p->get_state()->XPR[insn.rd()];

    uint32_t result = (uint32_t)acc;

    // Four signed INT8 multiplications
    for (int i = 0; i < 4; i++) {
        int8_t a_val = (int8_t)(a >> (i * 8));
        int8_t b_val = (int8_t)(b >> (i * 8));

        result += (uint32_t)((int32_t)a_val * (int32_t)b_val);
    }

    // Write result to destination register
    p->get_state()->XPR.write(insn.rd(), (reg_t)(int64_t)(int32_t)result);

    return pc + 4;
}


// DOT4 extension
class dot4_t : public extension_t
{
public:
    const char* name() const override {
        return "dot4";
    }

    // Instruction registration
    std::vector<insn_desc_t> get_instructions(
        const processor_t &) override
    {
        return {
            {
                0x0000000B,
                0xFE00707F,
                dot4, dot4, dot4, dot4,
                dot4, dot4, dot4, dot4
            }
        };
    }

    // Disassembler registration
    std::vector<disasm_insn_t*> get_disasms(
        const processor_t *) override
    {
        return {
            new disasm_insn_t(
                "dot4",
                0x0000000B,
                0xFE00707F,
                {&xrd, &xrs1, &xrs2}
            )
        };
    }
};


// Register extension
REGISTER_EXTENSION(dot4, []() {
    static dot4_t ext;
    return &ext;
})
