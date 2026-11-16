// Runs baseline and custom GELU on every generated test vector.
// Returns 0 only if both implementations match the expected result.

#include "../runtime/rt.h"
#include "../kernels/gelu/gelu.h"
#include "../tests/vectors/gelu_vectors.h"

int main(void)
{
    int failures = 0;

    for (int i = 0; i < GELU_NCASES; i++) {
        const gelu_case_t *c = &gelu_cases[i];

        int32_t base = gelu_baseline(c->input_q8);
        int32_t cust = gelu_custom(c->input_q8);

        int ok = (base == c->expected_q8) &&
                 (cust == c->expected_q8);

        failures += !ok;

        rt_puts(c->name);
        rt_puts(" input=");
        rt_puti(c->input_q8);
        rt_puts(" expected=");
        rt_puti(c->expected_q8);
        rt_puts(" baseline=");
        rt_puti(base);
        rt_puts(" custom=");
        rt_puti(cust);
        rt_puts(ok ? " PASS\n" : " FAIL\n");
    }

    rt_puts("Total cases: ");
    rt_puti(GELU_NCASES);
    rt_puts(" Failures: ");
    rt_puti(failures);
    rt_puts("\n");

    return failures;
}
