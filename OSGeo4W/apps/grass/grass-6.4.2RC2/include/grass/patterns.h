#ifndef _XGD_PATTERNS_H
#define _XGD_PATTERNS_H

#include "xgbitmaps.h"

/* Fill Patterns */

#define verticalpat_width 16
#define verticalpat_height 16
static BITMAPS_H_TYPE verticalpat_bits[] = {
    0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49,
    0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49,
    0x24, 0x49, 0x24, 0x49, 0x24, 0x49, 0x24, 0x49
};

#define check_width 16
#define check_height 16
static BITMAPS_H_TYPE check_bits[] = {
    0x24, 0x49, 0x24, 0x49, 0xff, 0xff, 0x24, 0x49, 0x24, 0x49, 0xff, 0xff,
    0x24, 0x49, 0x24, 0x49, 0xff, 0xff, 0x24, 0x49, 0x24, 0x49, 0xff, 0xff,
    0x24, 0x49, 0x24, 0x49, 0xff, 0xff, 0x24, 0x49
};

#define cross_width 16
#define cross_height 16
static BITMAPS_H_TYPE cross_bits[] = {
    0x49, 0x92, 0xb6, 0x6d, 0xb6, 0x6d, 0x49, 0x92, 0xb6, 0x6d, 0xb6, 0x6d,
    0x49, 0x92, 0xb6, 0x6d, 0xb6, 0x6d, 0x49, 0x92, 0xb6, 0x6d, 0xb6, 0x6d,
    0x49, 0x92, 0xb6, 0x6d, 0xb6, 0x6d, 0x49, 0x92
};

#define dot_dashed_width 16
#define dot_dashed_height 16
static BITMAPS_H_TYPE dot_dashed_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x87, 0xc3, 0x87, 0xc3, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

#define dotted_width 16
#define dotted_height 16
static BITMAPS_H_TYPE dotted_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x77, 0x77, 0x77, 0x77, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

#define horizpat_width 16
#define horizpat_height 16
static BITMAPS_H_TYPE horizpat_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00
};

#define long_dashed_width 16
#define long_dashed_height 16
static BITMAPS_H_TYPE long_dashed_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x0f, 0x78, 0x0f, 0x78, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

#define odd_dashed_width 16
#define odd_dashed_height 16
static BITMAPS_H_TYPE odd_dashed_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xb9, 0x31, 0xb9, 0x31, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

#define ptleft_width 16
#define ptleft_height 16
static BITMAPS_H_TYPE ptleft_bits[] = {
    0x24, 0x49, 0x49, 0x92, 0x92, 0x24, 0x24, 0x49, 0x49, 0x92, 0x92, 0x24,
    0x24, 0x49, 0x49, 0x92, 0x92, 0x24, 0x24, 0x49, 0x49, 0x92, 0x92, 0x24,
    0x24, 0x49, 0x49, 0x92, 0x92, 0x24, 0x24, 0x49
};

#define ptright_width 16
#define ptright_height 16
static BITMAPS_H_TYPE ptright_bits[] = {
    0x24, 0x49, 0x92, 0x24, 0x49, 0x92, 0x24, 0x49, 0x92, 0x24, 0x49, 0x92,
    0x24, 0x49, 0x92, 0x24, 0x49, 0x92, 0x24, 0x49, 0x92, 0x24, 0x49, 0x92,
    0x24, 0x49, 0x92, 0x24, 0x49, 0x92, 0x24, 0x49
};

#define short_dashed_width 16
#define short_dashed_height 16
static BITMAPS_H_TYPE short_dashed_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x0f, 0x0f, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

#define solidline_width 16
#define solidline_height 16
static BITMAPS_H_TYPE solidline_bits[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

#endif /* _XGD_PATTERNS_H */
