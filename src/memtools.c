/****************************************************************************
*
*   Copyright (c) 2017 Windhover Labs, L.L.C. All rights reserved.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions
* are met:
*
* 1. Redistributions of source code must retain the above copyright
*    notice, this list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright
*    notice, this list of conditions and the following disclaimer in
*    the documentation and/or other materials provided with the
*    distribution.
* 3. Neither the name Windhover Labs nor the names of its 
*    contributors may be used to endorse or promote products derived 
*    from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
* "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
* LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
* FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
* COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
* INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
* BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
* OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
* AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
* LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
* ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
* POSSIBILITY OF SUCH DAMAGE.
*
*****************************************************************************/
#include <limits.h>
#include <string.h>
#include <stddef.h>

/* TODO refactor. */
/*
#define PREPARE_FIRST_COPY()                                      \
    do {                                                          \
    if (bit_len >= (CHAR_BIT - dst_offset_modulo)) {              \
        *dst     &= reverse_mask[dst_offset_modulo];              \
        bit_len -= CHAR_BIT - dst_offset_modulo;                  \
    } else {                                                      \
        *dst     &= reverse_mask[dst_offset_modulo]               \
              | reverse_mask_xor[dst_offset_modulo + bit_len + 1];\
         c       &= reverse_mask[dst_offset_modulo + bit_len    ];\
        bit_len = 0;                                              \
    } } while (0)
*/

void memcpy_bitwise(char *dst_buf, unsigned int dst_offset, const char *src_buf, unsigned int src_offset, unsigned int bit_len)
{

    //static const uint8 mask[] =
    //    { 0x55, 0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7f, 0xff };
    static const char reverse_mask[] =
        { 0x55, 0x80, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc, 0xfe, 0xff };
    static const char reverse_mask_xor[] =
        { 0xff, 0x7f, 0x3f, 0x1f, 0x0f, 0x07, 0x03, 0x01, 0x00 };

    /* Null check */
    if (0 == src_buf || 0 == dst_buf)
    {
        goto end_of_function;
    }

    if (bit_len)
    {
        const char *src;
        char *dst;
        int src_offset_modulo;
        int dst_offset_modulo;

        src = src_buf + (src_offset / CHAR_BIT);
        dst = dst_buf + (dst_offset / CHAR_BIT);

        src_offset_modulo = src_offset % CHAR_BIT;
        dst_offset_modulo = dst_offset % CHAR_BIT;

        if (src_offset_modulo == dst_offset_modulo) 
        {
            int byte_len;
            int src_len_modulo;
            if (src_offset_modulo) 
            {
                char   c;
                c = reverse_mask_xor[dst_offset_modulo] & *src++;
                //PREPARE_FIRST_COPY();
                *dst++ |= c;
            }

            byte_len = bit_len / CHAR_BIT;
            src_len_modulo = bit_len % CHAR_BIT;

            if (byte_len) 
            {
                memcpy(dst, src, byte_len);
                src += byte_len;
                dst += byte_len;
            }

            if (src_len_modulo) 
            {
                *dst &= reverse_mask_xor[src_len_modulo];
                *dst |= reverse_mask[src_len_modulo]     & *src;
            }
        
        } 
        else 
        {
            int bit_diff_ls;
            int bit_diff_rs;
            int byte_len;
            int src_len_modulo;
            char c;

            /* Begin: Line things up on destination. */
            if (src_offset_modulo > dst_offset_modulo) 
            {
                bit_diff_ls = src_offset_modulo - dst_offset_modulo;
                bit_diff_rs = CHAR_BIT - bit_diff_ls;
    
                c = *src++ << bit_diff_ls;
                c |= *src >> bit_diff_rs;
                c     &= reverse_mask_xor[dst_offset_modulo];
            } 
            else 
            {
                bit_diff_rs = dst_offset_modulo - src_offset_modulo;
                bit_diff_ls = CHAR_BIT - bit_diff_rs;

                c = *src >> bit_diff_rs     &
                reverse_mask_xor[dst_offset_modulo];
            }
        
            //PREPARE_FIRST_COPY();
            *dst++ |= c;

            /* Middle: copy with only shifting the source. */
            byte_len = bit_len / CHAR_BIT;

            while (--byte_len >= 0) 
            {
                c = *src++ << bit_diff_ls;
                c |= *src >> bit_diff_rs;
                *dst++ = c;
            }

            /* End: copy the remaing bits. */
            src_len_modulo = bit_len % CHAR_BIT;
        
            if (src_len_modulo) 
            {
                c = *src++ << bit_diff_ls;
                c |= *src >> bit_diff_rs;
                c &= reverse_mask[src_len_modulo];

                *dst     &= reverse_mask_xor[src_len_modulo];
                *dst |= c;
            }
        }
    }
end_of_function:
    return;
}
