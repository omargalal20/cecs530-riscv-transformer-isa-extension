// Tiny runtime: print text to the terminal through Spike's HTIF syscall proxy.
#ifndef RT_H
#define RT_H
#include <stdint.h>

extern volatile uint32_t tohost[2];
extern volatile uint32_t fromhost[2];

static inline void rt_write(const char *buf, uint32_t len)
{
    static volatile uint64_t magic[8] __attribute__((aligned(64)));
    magic[0] = 64;                     // syscall number: write
    magic[1] = 1;                      // file descriptor: stdout
    magic[2] = (uint32_t)(uintptr_t)buf;
    magic[3] = len;
    __sync_synchronize();
    tohost[1] = 0;                     // high word first, so Spike never sees a half-written command
    tohost[0] = (uint32_t)(uintptr_t)magic;
    while (fromhost[0] == 0) { }       // wait for the host to finish
    fromhost[0] = 0;
    fromhost[1] = 0;
}

static inline void rt_puts(const char *s)
{
    uint32_t n = 0;
    while (s[n]) n++;
    rt_write(s, n);
}

static inline void rt_puti(int32_t v)
{
    char b[12];
    int i = 11;
    uint32_t u = (v < 0) ? (uint32_t)(-(int64_t)v) : (uint32_t)v;
    do { b[i--] = (char)('0' + u % 10); u /= 10; } while (u);
    if (v < 0) b[i--] = '-';
    rt_write(&b[i + 1], (uint32_t)(11 - i));
}
#endif
