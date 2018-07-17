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

#include "explain_app_test.h"
#include "../include/explain.h"
#include "../include/memtools.h"
#include "explain_test_utils.h"
#include "utils.h"
#include <stdlib.h>
#include "cfe_sb.h"
#include <stddef.h>

#define EXPLAIN_TEST_INPUT_PATH "test_input.json"

/* Test structure for source. Note uint8 padding. */
typedef struct
{
    uint8              TlmHeader[CFE_SB_TLM_HDR_SIZE];
    uint16             synch;

    uint8              padding;

    uint8              bit1:1;
    uint8              bit2:1;
    uint8              bit34:2;
    uint8              bit56:2;
    uint8              bit78:2;

    uint8              nibble1:4;
    uint8              nibble2:4;

    uint8              bl1, bl2;       /* boolean */
    int8               b1, b2, b3, b4;
    int16              w1,w2;
    int32              dw1, dw2;
    float              f1, f2;
    double             df1, df2;
    char               str[10];
} test_data_types_src;

/* Test structure for destination. Note uint16 padding. */
typedef struct
{
    uint8              TlmHeader[CFE_SB_TLM_HDR_SIZE];
    uint16             synch;

    uint16             padding;

    uint8              bit1:1;
    uint8              bit2:1;
    uint8              bit34:2;
    uint8              bit56:2;
    uint8              bit78:2;

    uint8              nibble1:4;
    uint8              nibble2:4;
    /* boolean */
    uint8              bl1, bl2;
    int8               b1, b2, b3, b4;
    int16              w1,w2;
    int32              dw1, dw2;
    float              f1, f2;
    double             df1, df2;

    char               str[10];
} test_data_types_dst;


typedef struct
{
    uint8              bit1:1;
    uint8              bit2:1;
    uint8              bit34:2;
    uint8              bit5678:4;
    uint8              padding;
} test_data_bit_fields;


void Explain_Test_Offsets(void)
{
    /* Input and output packets for test. */
    test_data_types_src src_pkt;
    test_data_types_dst dst_pkt;
    /* Pointers to input and output structs. */
    uint8 *src_ptr = (uint8 *) &src_pkt;
    uint8 *dst_ptr = (uint8 *) &dst_pkt;
    uint8 *temp_ptr = NULL;
    /* Pointer to the messsage definition. */
    explain_msg_t *msg_map_ptr     = NULL;
    explain_field_t *field_map_ptr = NULL;
    /* Variables for bitfield checks. */
    uint32 src_off_byte = 0;
    uint32 dst_off_byte = 0;
    uint32 src_off_bit  = 0;
    uint32 dst_off_bit  = 0;
    /* Message src symbol name. */
    char src_symbol[] = "test_data_types_src";

    /* initialize test environment to default state for every test */
    boolean returnBool = FALSE;
    explain_data_t app_data;
    (void) explain_init_data(&app_data);

    strncpy(&app_data.inputPath[0], EXPLAIN_TEST_INPUT_PATH, EXPLAIN_MAX_PATH_LENGTH);

    returnBool = validate_path(&app_data.inputPath[0]);
    if(FALSE == returnBool)
    {
        printf("validate path failed, exiting\n");
        exit(-1);
    }
    
    returnBool = explain_load_memory_map(&app_data.inputPath[0], &app_data);
    if(FALSE == returnBool)
    {
        printf("load memory map failed, exiting\n");
        /* cleanup test environment */
        explain_uninit_data(&app_data);
        exit(-1);
    }

    /* Clear buffers. */
    memset(&src_pkt, 0, sizeof(src_pkt));
    memset(&dst_pkt, 0, sizeof(dst_pkt));

    msg_map_ptr = explain_message_find_via_src_symbol(src_symbol, &app_data.message_list);

    for(field_map_ptr = list_head(msg_map_ptr->fields); 
        field_map_ptr != NULL; 
        field_map_ptr = list_item_next(field_map_ptr)) 
    {
        if(0 == strcmp(field_map_ptr->opName, "TlmHeader"))
        {
            UtAssert_True((offsetof(test_data_types_src, TlmHeader) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, TlmHeader) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "synch"))
        {
            UtAssert_True((offsetof(test_data_types_src, synch) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, synch) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "padding"))
        {
            UtAssert_True((offsetof(test_data_types_src, padding) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, padding) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "bit1"))
        {
            /* Check source by setting a bit. */
            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 7 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 7 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.bit1, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.bit1, "Test incorrect offset");

            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
            
        }
        else if(0 == strcmp(field_map_ptr->opName, "bit2"))
        {
            /* Check source by setting a bit. */

            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 7 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 7 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.bit2, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.bit2, "Test incorrect offset");
            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
        }
        else if(0 == strcmp(field_map_ptr->opName, "bit34"))
        {
            /* Check source by setting a bit. */
            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 6 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 6 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.bit34, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.bit34, "Test incorrect offset");
            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
        }
        else if(0 == strcmp(field_map_ptr->opName, "bit56"))
        {
            /* Check source by setting a bit. */
            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 6 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 6 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.bit56, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.bit56, "Test incorrect offset");
            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
        }
        else if(0 == strcmp(field_map_ptr->opName, "bit78"))
        {
            /* Check source by setting a bit. */
            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 6 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 6 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.bit78, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.bit78, "Test incorrect offset");
            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
        }
        else if(0 == strcmp(field_map_ptr->opName, "nibble1"))
        {
            /* Check source by setting a bit. */
            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 4 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 4 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.nibble1, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.nibble1, "Test incorrect offset");
            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
        }
        else if(0 == strcmp(field_map_ptr->opName, "nibble2"))
        {
            /* Check source by setting a bit. */
            src_off_byte = (field_map_ptr->srcOffset / 8);
            src_off_bit  = 4 - (field_map_ptr->srcOffset % 8);
            dst_off_byte = (field_map_ptr->dstOffset / 8);
            dst_off_bit  = 4 - (field_map_ptr->dstOffset % 8);
            
            temp_ptr = src_ptr + src_off_byte;
            *temp_ptr |= 1 << src_off_bit;
           
            temp_ptr = dst_ptr + dst_off_byte;
            *temp_ptr |= 1 << dst_off_bit;
            
            UtAssert_True(1 == src_pkt.nibble2, "Test incorrect offset");
            UtAssert_True(1 == dst_pkt.nibble2, "Test incorrect offset");
            /* Clear buffers. */
            memset(&src_pkt, 0, sizeof(src_pkt));
            memset(&dst_pkt, 0, sizeof(dst_pkt));
        }
        else if(0 == strcmp(field_map_ptr->opName, "bl1"))
        {
            UtAssert_True((offsetof(test_data_types_src, bl1) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, bl1) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "bl2"))
        {
            UtAssert_True((offsetof(test_data_types_src, bl2) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, bl2) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "b1"))
        {
            UtAssert_True((offsetof(test_data_types_src, b1) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, b1) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "b2"))
        {
            UtAssert_True((offsetof(test_data_types_src, b2) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, b2) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "b3"))
        {
            UtAssert_True((offsetof(test_data_types_src, b3) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, b3) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "b4"))
        {
            UtAssert_True((offsetof(test_data_types_src, b4) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, b4) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "w1"))
        {
            UtAssert_True((offsetof(test_data_types_src, w1) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, w1) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "w2"))
        {
            UtAssert_True((offsetof(test_data_types_src, w2) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, w2) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "dw1"))
        {
            UtAssert_True((offsetof(test_data_types_src, dw1) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, dw1) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "dw2"))
        {
            UtAssert_True((offsetof(test_data_types_src, dw2) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, dw2) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "f1"))
        {
            UtAssert_True((offsetof(test_data_types_src, f1) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, f1) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "f2"))
        {
            UtAssert_True((offsetof(test_data_types_src, f2) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, f2) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "df1"))
        {
            UtAssert_True((offsetof(test_data_types_src, df1) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, df1) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "df2"))
        {
            UtAssert_True((offsetof(test_data_types_src, df2) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, df2) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else if(0 == strcmp(field_map_ptr->opName, "str"))
        {
            UtAssert_True((offsetof(test_data_types_src, str) * 8) 
                    == field_map_ptr->srcOffset, "Test incorrect offset");
            UtAssert_True((offsetof(test_data_types_dst, str) * 8) 
                    == field_map_ptr->dstOffset, "Test incorrect offset");
        }
        else
        {
            /* Test should not encounter an extra field. */
            UtAssert_True(1 == 2, "Incorrect extra field");
        }
    }

    /* cleanup test environment */
    explain_uninit_data(&app_data);
}


void Explain_Test_Translation(void)
{

    /* Input and output buffers. */
    uint8 input_buffer[1024];
    uint8 output_buffer[1024];
    /* Pointers to input and output buffer. */
    uint8 *input_ptr = input_buffer;
    uint8 *output_ptr = output_buffer;
    /* Input and output packets for test. */
    test_data_types_src input_pkt;
    test_data_types_dst output_pkt;
    /* Test string. */
    char string_variable[10] = "ABCDEFGHIJ";
    /* Pointer to the messsage definition. */
    explain_msg_t *msg_def = NULL;
    /* Message src symbol name. */
    char src_symbol[] = "test_data_types_src";
    int16 i;
    /* Size written to destination buffer. */
    int size_written = 0;

    /* initialize test environment to default state for every test */
    boolean returnBool = FALSE;
    explain_data_t app_data;
    explain_init_data(&app_data);

    strncpy(&app_data.inputPath[0], EXPLAIN_TEST_INPUT_PATH, EXPLAIN_MAX_PATH_LENGTH);

    returnBool = validate_path(&app_data.inputPath[0]);
    if(FALSE == returnBool)
    {
        printf("validate path failed, exiting\n");
        exit(-1);
    }
    
    returnBool = explain_load_memory_map(&app_data.inputPath[0], &app_data);
    if(FALSE == returnBool)
    {
        printf("load memory map failed, exiting\n");
        /* cleanup test environment */
        explain_uninit_data(&app_data);
        exit(-1);
    }

    /* Clear buffers. */
    memset(&input_buffer, 0, sizeof(input_buffer));
    memset(&output_buffer, 0, sizeof(output_buffer));
    
    /* Clear output pkt, input_pkt is cleared in InitMsg. */
    memset(&output_pkt, 0, sizeof(output_pkt));
    
    /* Initialize data types packet. */
    CFE_SB_InitMsg(&input_pkt, 0x0881, 
            sizeof(input_pkt), TRUE);

    /* initialize the packet data with test values. */
    input_pkt.synch   = 0x6969;
    input_pkt.bit1    = 1;
    input_pkt.bit2    = 0;
    input_pkt.bit34   = 2;
    input_pkt.bit56   = 3;
    input_pkt.bit78   = 1;
    input_pkt.nibble1 = 0xA;
    input_pkt.nibble2 = 0x4;
    input_pkt.bl1     = FALSE;
    input_pkt.bl2     = TRUE;
    input_pkt.b1      = 16;
    input_pkt.b2      = 127;
    input_pkt.b3      = 0x7F;
    input_pkt.b4      = 0x45;
    input_pkt.w1      = 0x2468;
    input_pkt.w2      = 0x7FFF;
    input_pkt.dw1     = 0x12345678;
    input_pkt.dw2     = 0x87654321;
    input_pkt.f1      = 90.01;
    input_pkt.f2      = .0000045;
    input_pkt.df1     = 99.9;
    input_pkt.df2     = .4444;

    /* Copy the test string. */
    for (i=0; i < 10; ++i) 
    {
        input_pkt.str[i] = string_variable[i];
    }

    /* Copy the test packet into the input buffer. */
    memcpy(&input_buffer, &input_pkt, sizeof(input_pkt));

    msg_def = explain_message_find_via_src_symbol(src_symbol, &app_data.message_list);
    /* Translate the input buffer into the output buffer. */
    size_written = explain_translate_buffer((char *)output_ptr, (char *)input_ptr, msg_def, sizeof(output_buffer), EXPLAIN_FORWARD);

    /* Copy the output buffer to the output packet. */
    memcpy(&output_pkt, output_ptr, sizeof(output_pkt));

    /* cleanup test environment */
    explain_uninit_data(&app_data);

    /* Check results. */
    UtAssert_True(size_written > 0, "Test incorrect translation");
    UtAssert_True(input_pkt.synch    == output_pkt.synch, "Test incorrect translation");
    UtAssert_True(input_pkt.bit1     == output_pkt.bit1, "Test incorrect translation");
    UtAssert_True(input_pkt.bit2     == output_pkt.bit2, "Test incorrect translation");
    UtAssert_True(input_pkt.bit34    == output_pkt.bit34, "Test incorrect translation");
    UtAssert_True(input_pkt.bit56    == output_pkt.bit56, "Test incorrect translation");
    UtAssert_True(input_pkt.bit78    == output_pkt.bit78, "Test incorrect translation");
    UtAssert_True(input_pkt.nibble1  == output_pkt.nibble1, "Test incorrect translation");
    UtAssert_True(input_pkt.nibble2  == output_pkt.nibble2, "Test incorrect translation");
    UtAssert_True(input_pkt.bl1      == output_pkt.bl1, "Test incorrect translation");
    UtAssert_True(input_pkt.bl2      == output_pkt.bl2, "Test incorrect translation");
    UtAssert_True(input_pkt.b1       == output_pkt.b1, "Test incorrect translation");
    UtAssert_True(input_pkt.b2       == output_pkt.b2, "Test incorrect translation");
    UtAssert_True(input_pkt.b3       == output_pkt.b3, "Test incorrect translation");
    UtAssert_True(input_pkt.b4       == output_pkt.b4, "Test incorrect translation");
    UtAssert_True(input_pkt.w1       == output_pkt.w1, "Test incorrect translation");
    UtAssert_True(input_pkt.dw2      == output_pkt.dw2, "Test incorrect translation");
    UtAssert_True(input_pkt.f1       == output_pkt.f1, "Test incorrect translation");
    UtAssert_True(input_pkt.f2       == output_pkt.f2, "Test incorrect translation");
    UtAssert_True(input_pkt.df1      == output_pkt.df1, "Test incorrect translation");
    UtAssert_True(input_pkt.df2      == output_pkt.df2, "Test incorrect translation");
    for(i = 0; i < 10; ++i)
    {
        UtAssert_True(input_pkt.str[i] == output_pkt.str[i], "Test incorrect reverse translation");
    }
}


void Explain_Test_Reverse_Direction(void)
{
    /* Input and output buffers. */
    uint8 input_buffer[1024];
    uint8 output_buffer[1024];
    /* Pointers to input and output buffer. */
    uint8 *input_ptr = input_buffer;
    uint8 *output_ptr = output_buffer;
    /* Input and output packets for test. */
    /* swap input and output pkts. */
    test_data_types_src output_pkt;
    test_data_types_dst input_pkt;
    /* Test string. */
    char string_variable[10] = "ABCDEFGHIJ";
    /* Pointer to the messsage definition. */
    explain_msg_t *msg_def = NULL;
    /* Message src symbol name. */
    char src_symbol[] = "test_data_types_src";
    int16 i;
    /* Size written to destination buffer. */
    int size_written = 0;

    /* initialize test environment to default state for every test */
    boolean returnBool = FALSE;
    explain_data_t app_data;
    explain_init_data(&app_data);

    strncpy(&app_data.inputPath[0], EXPLAIN_TEST_INPUT_PATH, EXPLAIN_MAX_PATH_LENGTH);

    returnBool = validate_path(&app_data.inputPath[0]);
    if(FALSE == returnBool)
    {
        printf("validate path failed, exiting\n");
        exit(-1);
    }
    
    returnBool = explain_load_memory_map(&app_data.inputPath[0], &app_data);
    if(FALSE == returnBool)
    {
        printf("load memory map failed, exiting\n");
        /* cleanup test environment */
        explain_uninit_data(&app_data);
        exit(-1);
    }

    /* Clear buffers. */
    memset(&input_buffer, 0, sizeof(input_buffer));
    memset(&output_buffer, 0, sizeof(output_buffer));
    
    /* Clear output pkt, input_pkt is cleared in InitMsg. */
    memset(&output_pkt, 0, sizeof(output_pkt));
    
    /* Initialize data types packet. */
    CFE_SB_InitMsg(&input_pkt, 0x0881, 
            sizeof(input_pkt), TRUE);

    /* initialize the packet data with test values. */
    input_pkt.synch   = 0x6969;
    input_pkt.bit1    = 1;
    input_pkt.bit2    = 0;
    input_pkt.bit34   = 2;
    input_pkt.bit56   = 3;
    input_pkt.bit78   = 1;
    input_pkt.nibble1 = 0xA;
    input_pkt.nibble2 = 0x4;
    input_pkt.bl1     = FALSE;
    input_pkt.bl2     = TRUE;
    input_pkt.b1      = 16;
    input_pkt.b2      = 127;
    input_pkt.b3      = 0x7F;
    input_pkt.b4      = 0x45;
    input_pkt.w1      = 0x2468;
    input_pkt.w2      = 0x7FFF;
    input_pkt.dw1     = 0x12345678;
    input_pkt.dw2     = 0x87654321;
    input_pkt.f1      = 90.01;
    input_pkt.f2      = .0000045;
    input_pkt.df1     = 99.9;
    input_pkt.df2     = .4444;

    /* Copy the test string. */
    for (i=0; i < 10; ++i) 
    {
        input_pkt.str[i] = string_variable[i];
    }

    /* Copy the test packet into the input buffer. */
    memcpy(&input_buffer, &input_pkt, sizeof(input_pkt));

    msg_def = explain_message_find_via_src_symbol(src_symbol, &app_data.message_list);
    /* Translate the input buffer into the output buffer. */
    size_written = explain_translate_buffer((char *)output_ptr, (char *)input_ptr, msg_def, sizeof(output_buffer), EXPLAIN_REVERSE);

    /* Copy the output buffer to the output packet. */
    memcpy(&output_pkt, output_ptr, sizeof(output_pkt));

    /* cleanup test environment */
    explain_uninit_data(&app_data);

    /* Check results. */
    UtAssert_True(size_written > 0, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.synch    == output_pkt.synch, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bit1     == output_pkt.bit1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bit2     == output_pkt.bit2, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bit34    == output_pkt.bit34, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bit56    == output_pkt.bit56, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bit78    == output_pkt.bit78, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.nibble1  == output_pkt.nibble1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.nibble2  == output_pkt.nibble2, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bl1      == output_pkt.bl1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.bl2      == output_pkt.bl2, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.b1       == output_pkt.b1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.b2       == output_pkt.b2, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.b3       == output_pkt.b3, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.b4       == output_pkt.b4, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.w1       == output_pkt.w1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.dw2      == output_pkt.dw2, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.f1       == output_pkt.f1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.f2       == output_pkt.f2, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.df1      == output_pkt.df1, "Test incorrect reverse translation");
    UtAssert_True(input_pkt.df2      == output_pkt.df2, "Test incorrect reverse translation");
    for(i = 0; i < 10; ++i)
    {
        UtAssert_True(input_pkt.str[i] == output_pkt.str[i], "Test incorrect reverse translation");
    }
}


void Explain_Test_Bitwise_Memcpy(void)
{
    /* Test source buffer. */
    uint8 src_buf[8]  = {0, 0, 0, 0, 1, 2, 3, 4};
    /* Test destination buffer. */
    uint8 dst_buf[8]  = {0};
    /* Source offset. */
    uint32 src_offset = 32;
    /* Destination offset. */
    uint32 dst_offset = 0;
    /* Bit length to copy. */
    uint32 bit_len    = 32;

    /* Test for endianness. */
    int32 a = 0x12345678;
    uint8 *c = (uint8*)(&a);
    if (*c != 0x78) 
    {
        printf("big-endian, skipping test Explain_Test_Bitwise_Memcpy\n");
        goto end_of_function;
    }

    /* Call function under test. */
    memcpy_bitwise((char *)&dst_buf[0], dst_offset, (char *)&src_buf[0], src_offset, bit_len);

    /* Verify destination. */
    UtAssert_True(dst_buf[0] == 1, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[1] == 2, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[2] == 3, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[3] == 4, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[4] == 0, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[5] == 0, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[6] == 0, "Test bitwise memcpy destination");
    UtAssert_True(dst_buf[7] == 0, "Test bitwise memcpy destination");

    /* Verify source. */
    UtAssert_True(src_buf[0] == 0, "Test bitwise memcpy source");
    UtAssert_True(src_buf[1] == 0, "Test bitwise memcpy source");
    UtAssert_True(src_buf[2] == 0, "Test bitwise memcpy source");
    UtAssert_True(src_buf[3] == 0, "Test bitwise memcpy source");
    UtAssert_True(src_buf[4] == 1, "Test bitwise memcpy source");
    UtAssert_True(src_buf[5] == 2, "Test bitwise memcpy source");
    UtAssert_True(src_buf[6] == 3, "Test bitwise memcpy source");
    UtAssert_True(src_buf[7] == 4, "Test bitwise memcpy source");

end_of_function:
    return;
}


/* Todo this test makes some assumptions. By the C standard, 
 * the compiler is free to store the bit field any random way. Also,
 * the test assumes little endianness. Todo for getting the memory
 * map from the python utility and making this test independent of
 * endianness and random bit field order. */
void Explain_Test_Bitwise_Memcpy_BitFields(void)
{
    /* Todo assumes little endianness */
    /* bit5678, bit34, bit2, bit1 */
    /* 0000     00     0     0 */
    test_data_bit_fields bit_fields  = {1, 0, 0, 0};
    test_data_bit_fields bit_test    = {0};
    uint8 i = 0;
    /* Expected results for initial iteration.  */
    uint8 expected1 = 1;
    uint8 expected2 = 0;
    uint8 expected34 = 0;
    uint8 expected5678 = 0;

    /* Bit test offsets and lengths. */
    uint32 bit_test_dst_offset       = 7;
    uint32 bit_test_src_offset       = 7;
    uint32 bit_test_length           = 1;

    int32 a = 0x12345678;
    uint8 *c = (uint8*)(&a);
    if (*c != 0x78) 
    {
        printf("big-endian, skipping test Explain_Test_Bitwise_Memcpy_BitFields\n");
        goto end_of_function;
    }

    /* Test for bit packing. */
    test_data_bit_fields pack_check  = {1, 0, 0, 0};
    uint8 * check_ptr = (uint8 *) &pack_check + 1;
    if(1 == (*check_ptr & 1 << 0))
    {
        printf("bit field randomly packed, skipping test Explain_Test_Bitwise_Memcpy_BitFields\n");
        goto end_of_function;
    }
    
    pack_check.bit1 = 0;
    pack_check.bit2 = 1;

    if(1 == (*check_ptr & 1 << 1))
    {
        printf("bit field randomly packed, skipping test Explain_Test_Bitwise_Memcpy_BitFields\n");
        goto end_of_function;
    }

    pack_check.bit2 = 0;
    pack_check.bit34 = 1;

    if(1 == (*check_ptr & 1 << 2))
    {
        printf("bit field randomly packed, skipping test Explain_Test_Bitwise_Memcpy_BitFields\n");
        goto end_of_function;
    }

    pack_check.bit34 = 0;
    pack_check.bit5678 = 1;

    if(1 == (*check_ptr & 1 << 4))
    {
        printf("bit field randomly packed, skipping test Explain_Test_Bitwise_Memcpy_BitFields\n");
        goto end_of_function;
    }

    /* First test portion single bit copy checks. */
    for(i = 0; i < 8; ++i)
    {
        /* Call function under test. */
        memcpy_bitwise((char *)&bit_test, bit_test_dst_offset, (char *)&bit_fields, bit_test_src_offset, bit_test_length);

        /* Evaluate results bit_test */
        UtAssert_True(bit_test.bit1 == expected1, "Test bitwise memcpy bit fields");
        UtAssert_True(bit_test.bit2 == expected2, "Test bitwise memcpy bit fields");
        UtAssert_True(bit_test.bit34 == expected34, "Test bitwise memcpy bit fields");
        UtAssert_True(bit_test.bit5678 == expected5678, "Test bitwise memcpy bit fields");

        /* Decrement the destination offset to copy to the next bit
         * in the destination structure. */
        bit_test_dst_offset--;

        /* Update the expected results. */
        if(0 == i)
        {
            expected1 = 0;
            expected2 = 1;
        }
        else if (1 == i)
        {
            expected2 = 0;
            expected34 = 1;
        }
        else if (2 == i)
        {
            expected34 = 2;
        }
        else if (3 == i)
        {
            expected34 = 0;
            expected5678 = 1;
        }
        else if (4 == i)
        {
            expected5678 = 2;
        }
        else if (5 == i)
        {
            expected5678 = 4;
        }
        else if (6 == i)
        {
            expected5678 = 8;
        }

        /* Reset bit_test */
        memset(&bit_test, 0, sizeof(bit_test));
    }
    /* Second test portion multiple bit copy checks. */
    bit_test_dst_offset = 6;
    bit_test_src_offset = 4;
    bit_test_length     = 2;
    /* Reset bit_test. */
    memset(&bit_test, 0, sizeof(bit_test));
    /* Reset bit_fields. */
    memset(&bit_fields, 0, sizeof(bit_fields));

    
    bit_fields.bit34 = 3;

    /* Set expected results. */
    expected1    = 1;
    expected2    = 1;
    expected34   = 0;
    expected5678 = 0;

    /* Call function under test. */
    memcpy_bitwise((char *)&bit_test, bit_test_dst_offset, (char *)&bit_fields, bit_test_src_offset, bit_test_length);

    /* Evaluate results bit_test. */
    UtAssert_True(bit_test.bit1 == expected1, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit2 == expected2, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit34 == expected34, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit5678 == expected5678, "Test bitwise memcpy bit fields");

    /* Reset bit_test. */
    memset(&bit_test, 0, sizeof(bit_test));
    /* Set expected results. */
    expected1    = 0;
    expected2    = 0;
    expected34   = 3;
    expected5678 = 0;
    /* Moved destination offset. */
    bit_test_dst_offset = 4;

    /* Call function under test. */
    memcpy_bitwise((char *)&bit_test, bit_test_dst_offset, (char *)&bit_fields, bit_test_src_offset, bit_test_length);

    /* Evaluate results bit_test. */
    UtAssert_True(bit_test.bit1 == expected1, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit2 == expected2, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit34 == expected34, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit5678 == expected5678, "Test bitwise memcpy bit fields");

    /* Reset bit_test. */
    memset(&bit_test, 0, sizeof(bit_test));
    /* Set expected results. */
    expected1    = 0;
    expected2    = 0;
    expected34   = 0;
    expected5678 = 3;
    /* Moved destination offset. */
    bit_test_dst_offset = 2;

    /* Call function under test. */
    memcpy_bitwise((char *)&bit_test, bit_test_dst_offset, (char *)&bit_fields, bit_test_src_offset, bit_test_length);

    /* Evaluate results bit_test. */
    UtAssert_True(bit_test.bit1 == expected1, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit2 == expected2, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit34 == expected34, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit5678 == expected5678, "Test bitwise memcpy bit fields");

    /* Reset bit_test. */
    memset(&bit_test, 0, sizeof(bit_test));
    /* Set expected results. */
    expected1    = 0;
    expected2    = 0;
    expected34   = 0;
    expected5678 = 12;
    /* Moved destination offset. */
    bit_test_dst_offset = 0;

    /* Call function under test. */
    memcpy_bitwise((char *)&bit_test, bit_test_dst_offset, (char *)&bit_fields, bit_test_src_offset, bit_test_length);

    /* Evaluate results bit_test. */
    UtAssert_True(bit_test.bit1 == expected1, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit2 == expected2, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit34 == expected34, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit5678 == expected5678, "Test bitwise memcpy bit fields");

    /* Third test portion nibble bit copy checks. */
    bit_test_dst_offset = 4;
    bit_test_src_offset = 0;
    bit_test_length     = 4;
    /* Reset bit_test. */
    memset(&bit_test, 0, sizeof(bit_test));
    /* Reset bit_fields. */
    memset(&bit_fields, 0, sizeof(bit_fields));
    
    bit_fields.bit5678 = 15;

    /* Set expected results. */
    expected1    = 1;
    expected2    = 1;
    expected34   = 3;
    expected5678 = 0;

    /* Call function under test. */
    memcpy_bitwise((char *)&bit_test, bit_test_dst_offset, (char *)&bit_fields, bit_test_src_offset, bit_test_length);

    /* Evaluate results bit_test. */
    UtAssert_True(bit_test.bit1 == expected1, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit2 == expected2, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit34 == expected34, "Test bitwise memcpy bit fields");
    UtAssert_True(bit_test.bit5678 == expected5678, "Test bitwise memcpy bit fields");

end_of_function:
    return;
}


void Explain_App_Test_AddTestCases(void)
{
    UtTest_Add(Explain_Test_Offsets,             Explain_Test_Setup, Explain_Test_TearDown, "Explain_Test_Offsets");
    UtTest_Add(Explain_Test_Translation,         Explain_Test_Setup, Explain_Test_TearDown, "Explain_Test_Translation");
    UtTest_Add(Explain_Test_Reverse_Direction,   Explain_Test_Setup, Explain_Test_TearDown, "Explain_Test_Reverse_Direction");
    UtTest_Add(Explain_Test_Bitwise_Memcpy,      Explain_Test_Setup, Explain_Test_TearDown, "Explain_Test_Bitwise_Memcpy");
    UtTest_Add(Explain_Test_Bitwise_Memcpy_BitFields, Explain_Test_Setup, Explain_Test_TearDown, "Explain_Test_Bitwise_Memcpy_BitFields");
} /* end Explain_App_Test_AddTestCases */

/************************/
/*  End of File Comment */
/************************/
