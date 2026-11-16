
#ifndef GELU_LUT_H
#define GELU_LUT_H

#include <stdint.h>

// Tanh lookup table in Q15 fixed-point format.
//
// 65 entries cover [0, 4] with a spacing of 1/16.
// Each entry is round(tanh(i / 16) * 32768).
//
// Negative inputs use tanh's odd symmetry.
// Values outside [-4, 4] use the endpoint values.

static const int32_t gelu_tanh_lut_q15[65] = {
        0,  2045,  4075,  6073,  8025,  9919, 11743, 13486,
    15143, 16706, 18173, 19542, 20813, 21986, 23066, 24054,
    24956, 25776, 26519, 27191, 27797, 28341, 28830, 29268,
    29660, 30010, 30322, 30600, 30847, 31067, 31262, 31435,
    31589, 31726, 31846, 31953, 32048, 32132, 32206, 32271,
    32329, 32381, 32426, 32466, 32501, 32532, 32560, 32584,
    32606, 32625, 32642, 32657, 32670, 32681, 32691, 32700,
    32708, 32715, 32721, 32727, 32732, 32736, 32740, 32743,
    32746
};

#endif
