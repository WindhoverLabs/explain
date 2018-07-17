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
#include "message.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>


/* Initialize a message. */
static void message_clear(explain_msg_t *msg_ptr);


/* Allocate a new message. */
static explain_msg_t *message_allocate(void);


/* Allocate a new field. */
static explain_field_t *field_allocate(void);


/* Cleanup all messages. */
static void purge_messages(explain_msg_list_t *handle);


/* Free a message. */
static void message_free(explain_msg_t *msg_ptr);


/* Free a field. */
static void field_free(explain_field_t *field_ptr);


void explain_message_init(explain_msg_list_t *handle)
{
    /* Initialize the outer linked list. */
    LIST_STRUCT_INIT(handle, messages);
}


void explain_message_deinit(explain_msg_list_t *handle)
{
    purge_messages(handle);
}


static void message_clear(explain_msg_t *msg_ptr)
{
    /* Initialize the inner linked list. */
    LIST_STRUCT_INIT(msg_ptr, fields);
}


static explain_msg_t *message_allocate(void)
{
    explain_msg_t *msg_ptr = NULL;

    msg_ptr = (explain_msg_t*) malloc(sizeof(explain_msg_t));
    if(NULL == msg_ptr)
    {
        /* TODO error condition */
        printf("message_allocate failed\n");
        goto end_of_function;
    }

end_of_function:

    return (msg_ptr);

}


static explain_field_t *field_allocate(void)
{
    explain_field_t *field_ptr = NULL;

    field_ptr = (explain_field_t*) malloc(sizeof(explain_field_t));
    if(NULL == field_ptr)
    {
        /* TODO error condition */
        printf("field_allocate failed\n");
    }

    return (field_ptr);
}


explain_msg_t *explain_message_add(explain_msg_list_t *handle)
{
    explain_msg_t *msg_ptr = NULL;

    if(0 == handle)
    {
        printf("Null pointer in message message_add\n");
        goto end_of_function;
    }

    msg_ptr = message_allocate();
    if(NULL == msg_ptr) 
    {
        /* TODO error condition */
        printf("message_add failed\n");
        goto end_of_function;
    }

    /* Initialize the allocated message. */
    message_clear(msg_ptr);

    /* Add the new message to the list. */
    list_add(handle->messages, msg_ptr);

end_of_function:
    return msg_ptr;
}


explain_field_t *explain_field_add(explain_msg_t *msg_ptr, const explain_field_t *addition)
{
    explain_field_t *field_ptr = NULL;

    if(0 == msg_ptr || 0 == addition)
    {
        printf("Null pointer in message field_add\n");
        goto end_of_function;
    }

    field_ptr = field_allocate();
    if(NULL == field_ptr) 
    {
        /* TODO error condition */
        printf("field_add failed\n");
        goto end_of_function;
    }

    /* Copy fields. */
    memcpy(field_ptr, addition, sizeof(explain_field_t));

    /* Add the new field to the list. */
    list_add(msg_ptr->fields, field_ptr);

end_of_function:
    return field_ptr;
}


static void purge_messages(explain_msg_list_t *handle)
{
    explain_msg_t *msg_ptr  = NULL;
    explain_msg_t *msg_next = NULL;

    for(msg_ptr = list_head(handle->messages); msg_ptr != NULL;) 
    {
        msg_next = msg_ptr->next;
        message_free(msg_ptr);
        msg_ptr = msg_next;
    }
}


static void message_free(explain_msg_t *msg_ptr)
{
    explain_field_t *field_ptr = NULL;

    if(0 != msg_ptr)
    {
        while((field_ptr = list_pop(msg_ptr->fields)) != NULL) 
        {
            field_free(field_ptr);
        }
        
        free(msg_ptr);
    }
    else
    {
        printf("Null pointer in message free\n");
    }
}


static void field_free(explain_field_t *field_ptr)
{
    if(0 != field_ptr)
    {
        free(field_ptr);
    }
    else
    {
        printf("Null pointer in field free\n");
    }
}


explain_msg_t * explain_message_find_via_id(unsigned int id, explain_msg_list_t *handle)
{
    explain_msg_t *msg_ptr = NULL;

    if(0 == handle)
    {
        printf("Null pointer in message_find_via_id\n");
        goto end_of_function;
    }

    for(msg_ptr = list_head(handle->messages); 
        msg_ptr != NULL; 
        msg_ptr = list_item_next(msg_ptr))
    {
        if(id == msg_ptr->id) 
        {
            return msg_ptr;
        }
    }

end_of_function:
    return NULL;
}


explain_msg_t * explain_message_find_via_name(const char *ops_name, explain_msg_list_t *handle)
{
    explain_msg_t *msg_ptr = NULL;

    if(0 == handle || 0 == ops_name)
    {
        printf("Null pointer in message_find_via_name\n");
        goto end_of_function;
    }

    for(msg_ptr = list_head(handle->messages); 
        msg_ptr != NULL; 
        msg_ptr = list_item_next(msg_ptr))
    {
        if(0 == strcmp(msg_ptr->opsName, ops_name)) 
        {
            return msg_ptr;
        }
    }

end_of_function:
    return NULL;
}


explain_msg_t * explain_message_find_via_src_symbol(const char *src_symbol, explain_msg_list_t *handle)
{
    explain_msg_t *msg_ptr = NULL;

    if(0 == handle || 0 == src_symbol)
    {
        printf("Null pointer in message_find_via_src_symbol\n");
        goto end_of_function;
    }

    for(msg_ptr = list_head(handle->messages); 
        msg_ptr != NULL; 
        msg_ptr = list_item_next(msg_ptr))
    {
        if(0 == strcmp(msg_ptr->srcSymbol, src_symbol)) 
        {
            return msg_ptr;
        }
    }

end_of_function:
    return NULL;
}


explain_msg_t * explain_message_find_via_dst_symbol(const char *dst_symbol, explain_msg_list_t *handle)
{
    explain_msg_t *msg_ptr = NULL;

    if(0 == handle || 0 == dst_symbol)
    {
        printf("Null pointer in message_find_via_dst_symbol\n");
        goto end_of_function;
    }

    for(msg_ptr = list_head(handle->messages); 
        msg_ptr != NULL; 
        msg_ptr = list_item_next(msg_ptr))
    {
        if(0 == strcmp(msg_ptr->dstSymbol, dst_symbol)) 
        {
            return msg_ptr;
        }
    }

end_of_function:
    return NULL;
}


void explain_print_all_fields(explain_msg_list_t *handle)
{
    explain_field_t *field_ptr = NULL;
    explain_msg_t *msg_ptr     = NULL;

    for(msg_ptr = list_head(handle->messages); 
        msg_ptr != NULL; 
        msg_ptr = list_item_next(msg_ptr))
    {
        /* Print the message info. */
        printf("opsName %s\n", msg_ptr->opsName);
        printf("dstSymbol %s\n", msg_ptr->dstSymbol);
        printf("srcSymbol %s\n", msg_ptr->srcSymbol);
        printf("srcEndian %d\n", msg_ptr->srcEndian);
        printf("dstEndian %d\n", msg_ptr->dstEndian);
        printf("id %d\n", msg_ptr->id);
    
        /* Print all the field info. */
        for(field_ptr = list_head(msg_ptr->fields); 
            field_ptr != NULL; 
            field_ptr = list_item_next(field_ptr)) 
        {
            printf("opName %s\n", field_ptr->opName);
            printf("length %u\n", field_ptr->length);
            printf("srcOffset %u\n", field_ptr->srcOffset);
            printf("dstOffset %u\n", field_ptr->dstOffset);
        }
    }
}



