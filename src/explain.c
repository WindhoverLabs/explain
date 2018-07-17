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
/* Local includes */
#include "explain.h"
#include "memtools.h"
#include "parser.h"
#include "utils.h"
/* Lib includes */
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>


/* Regular copy from source to destination. */
static void copy_field_forward(char *dst_buf, const char *src_buf, explain_field_t *field_ptr);


/* Reverse copy from destination to source. */
static void copy_field_reverse(char *dst_buf, const char *src_buf, explain_field_t *field_ptr);


static void copy_field_forward(char *dst_buf, const char *src_buf, explain_field_t *field_ptr)
{
    memcpy_bitwise(dst_buf, field_ptr->dstOffset, src_buf, field_ptr->srcOffset, field_ptr->length);
}


static void copy_field_reverse(char *dst_buf, const char *src_buf, explain_field_t *field_ptr)
{
    memcpy_bitwise(dst_buf,  field_ptr->srcOffset, src_buf, field_ptr->dstOffset, field_ptr->length);
}


int explain_translate_buffer(char *dst, const char *src, const explain_msg_t *msg_def, unsigned int max_len, explain_direction_t direction)
{
    explain_field_t *field_map_ptr        = 0;
    unsigned int size_written     = 0;
    /* Padding can be negative if parsing out of order bit-field. */
    int padding                   = 0;

    /* Null pointer checks */
    if (0 == src || 0 == dst || 0 == msg_def)
    {
        goto end_of_function;
    }

    /* Clear the destination buffer. */
    memset((void*)dst, 0, max_len);

    for(field_map_ptr = list_head(msg_def->fields); 
        field_map_ptr != 0; 
        field_map_ptr = list_item_next(field_map_ptr)) 
    {
        if (direction == EXPLAIN_FORWARD)
        {
            /* Calculate any padding between current and last field. */
            padding = field_map_ptr->dstOffset - size_written;

            /* Check size to not exceed destination buffer. */
            if((field_map_ptr->length + size_written + padding) <= max_len * 8)
            {
                /* Copy the field. */
                copy_field_forward(dst, src, field_map_ptr);
                /* Add to the total size written. */
                size_written += field_map_ptr->length + padding;
            }
            else
            {
                /* Destination buffer is not large enough. */
                size_written = -1;
                errno = ENOMEM;
                goto end_of_function;
            }
        }
        else if (direction == EXPLAIN_REVERSE)
        {
            /* Calculate any padding between current and last field. */
            padding = field_map_ptr->srcOffset - size_written;

            /* Check size to not exceed destination buffer. */
            if((field_map_ptr->length + size_written + padding) <= max_len * 8)
            {
                /* Copy the field. */
                copy_field_reverse(dst, src, field_map_ptr);
                /* Add to the total size written. */
                size_written += field_map_ptr->length + padding;
            }
            else
            {
                /* Destination buffer is not large enough. */
                size_written = -1;
                errno = ENOMEM;
                goto end_of_function;
            }
        }
        else
        {
            /* Do nothing */
            printf("Unknown option in translate buffer\n");
        }

    }

    /* Check for bits copied. */
    if(size_written % 8 != 0)
    {
        /*
         * Check that +1 byte would fit in the destination buffer. 
         * Ensure future size read access will not go out of bounds. 
         */
        if((size_written / 8) + 1 <= max_len)
        {
            size_written = (size_written / 8) + 1;
        }
    }
    else
    {
        size_written = size_written / 8;
    }

end_of_function:
    return size_written;
}


bool explain_load_memory_map(const char *filepath, explain_data_t *handle)
{
    bool returnBool = true;
    uint32_t recursive_count = 0;

    /* Null pointer checks. */
    if(0 == filepath || 0 == handle)
    {
        returnBool = false;
        printf("Null pointer in explain_load_memory_map\n");
        goto end_of_function;
    }

    returnBool = read_input(filepath, &handle->rawInput[0]);
    if(false == returnBool)
    {
        goto end_of_function;
    }

    /* TODO error checking 
     * convert to json_tokener_parse_ex
     * */
    json_object * jobj = json_tokener_parse(&handle->rawInput[0]);
    returnBool = json_parse(jobj, &recursive_count, handle);

end_of_function:
    return returnBool;
}


bool explain_init_data(explain_data_t *app_data)
{

    bool returnBool = true;
    /* Null pointer checks. */
    if(0 != app_data)
    {
        /* Initialize application data. */
        memset((void*)app_data, 0x00, sizeof(app_data));
        /* Initialize linked list. */
        explain_message_init(&app_data->message_list);
        /* Get the first message. */
        app_data->currentMsg = explain_message_add(&app_data->message_list);
        /* */
        if (0 == app_data->currentMsg)
        {
            returnBool = false;
        }
    }
    else
    {
        returnBool = false;
        printf("Null pointer in explain_init_data\n");
    }

    return returnBool;
}


void explain_uninit_data(explain_data_t *app_data)
{
    /* Null pointer checks. */
    if(0 != app_data)
    {
        explain_message_deinit(&app_data->message_list);
    }
    else
    {
        printf("Null pointer in explain_uninit_data\n");
    }
}


