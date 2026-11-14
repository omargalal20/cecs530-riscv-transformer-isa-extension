// Runs the baseline and custom dot-product kernels on every test vector.
// Returns 0 only if both match the expected value computed by Python.
#include "../runtime/rt.h"
#include "../kernels/dot/dot.h"
#include "../tests/vectors/dot_vectors.h"

int main(void)
{
    int failures = 0;
    for (int i = 0; i < DOT_NCASES; i++) {
        const dot_case_t *c = &dot_cases[i];
        int32_t base = dot_baseline(c->a, c->b, c->n);
        int32_t cust = dot_custom(c->a, c->b, c->n);
        int ok = (base == c->expected) && (cust == c->expected);
        failures += !ok;
        rt_puts(c->name);
        rt_puts(" n=");        rt_puti(c->n);
        rt_puts(" expected="); rt_puti(c->expected);
        rt_puts(" base=");     rt_puti(base);
        rt_puts(" custom=");   rt_puti(cust);
        rt_puts(ok ? " PASS\n" : " FAIL\n");
    }
    return failures;
}
