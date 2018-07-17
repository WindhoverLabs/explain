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
#include "explain.h"
#include "usage.h"
#include "common_types.h"
#include "cfe_sb.h"
#include "utils.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>


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


int main(int argc, char *argv[])
{
    int exitCode = EXIT_SUCCESS;
    boolean returnBool = FALSE;
    explain_msg_t *msg_map_ptr     = NULL;
    explain_field_t *field_map_ptr = NULL;
    /* Message src symbol name. */
    char src_symbol[] = "test_data_types_src";
    /* Message dst symbol name. */
    char dst_symbol[] = "test_data_types_dst";
    /* Message id. */
    uint32 msg_id     = 2177;
    /* Ops name. */
    char ops_name[]   = "";
    /* Input and output packets for test. */
    test_data_types_src src_pkt;
    test_data_types_dst dst_pkt;
    /* Pointers to input and output structs. */
    uint8 *src_ptr = (uint8 *) &src_pkt;
    uint8 *dst_ptr = (uint8 *) &dst_pkt;
    /* Size written to destination buffer. */
    int size_written = 0;

    /* Clear packets. */
    memset(src_ptr, 0, sizeof(src_pkt));
    memset(dst_ptr, 0, sizeof(dst_pkt));

    /* Application data. */
    explain_data_t app_data;

    /* Initialize application data */
    (void) explain_init_data(&app_data);

    /* Parse args and get the input file path */
    returnBool = parse_options(&app_data.inputPath[0], argc, argv);
    if(FALSE == returnBool)
    {
        printf("Parse options failed \n");
        exitCode = EXIT_FAILURE;
        goto end_of_function;
    }
    
    /* Validate the path argument */
    returnBool = validate_path(&app_data.inputPath[0]);
    if(FALSE == returnBool)
    {
        printf("Validate path failed \n");
        exitCode = EXIT_FAILURE;
        goto end_of_function;
    }

    /* Read in the input file */
    returnBool = explain_load_memory_map(&app_data.inputPath[0], &app_data);
    if(FALSE == returnBool)
    {
        printf("Load memory map failed \n");
        exitCode = EXIT_FAILURE;
        goto end_of_function;
    }

    /* Print everything. */
    printf("Begin dump of parsed memory map.\n");
    explain_print_all_fields(&app_data.message_list);
    printf("End dump of parsed memory map.\n");

    /* Lookup message by source symbol name. */
    msg_map_ptr = explain_message_find_via_src_symbol(src_symbol, &app_data.message_list);
    /* Lookup message by destination symbol name. */
    msg_map_ptr = explain_message_find_via_dst_symbol(dst_symbol, &app_data.message_list);
    /* Lookup message by ops name. */
    msg_map_ptr = explain_message_find_via_name(ops_name, &app_data.message_list);
    /* Lookup message by message id. */
    msg_map_ptr = explain_message_find_via_id(msg_id, &app_data.message_list);

    /* Set a field to a value. */
    src_pkt.synch = 2;

    /* Translate from source to destination. */
    printf("Translate from source to destination.\n");
    size_written = explain_translate_buffer(src_ptr, dst_ptr, msg_map_ptr, sizeof(dst_pkt), EXPLAIN_FORWARD);

    printf("src_pkt.synch == %u\n", src_pkt.synch);
    printf("dst_pkt.synch == %u\n", dst_pkt.synch);
    printf("size_written = %d\n", size_written);
    printf("size of destination packet %lu\n",sizeof(dst_pkt));
    printf("size of src packet %lu\n",sizeof(src_pkt));

    explain_uninit_data(&app_data);

end_of_function:

    return exitCode;
}
