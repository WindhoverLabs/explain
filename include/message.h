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
#ifndef MESSAGE_H
#define MESSAGE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "list.h"
#include "config.h"


/** 
**  \brief enum for Endianness.
*/
typedef enum 
{
    /** \brief Little Endian. */
    EXPLAIN_LITTLE_ENDIAN = 0,
    /** \brief Big Endian. */
    EXPLAIN_BIG_ENDIAN    = 1
} explain_endianess_t;


/** 
**  \brief A source / destination description of a field.
*/
typedef struct explain_field
{
    /** \brief Pointer to next field. Must be first. */
    struct explain_field *next;
    /** \brief opsname alias for the field. */
    char opName[EXPLAIN_MAX_OPS_NAME_LENGTH];
    /** \brief Length of the field. */
    unsigned int length;
    /** \brief Source offset. */
    unsigned int srcOffset;
    /** \brief Destination offset. */
    unsigned int dstOffset;
} explain_field_t;


/** 
**  \brief A source / destination description of a field.
*/
typedef struct explain_msg
{
    /** \brief Pointer to next message. Must be first. */
    struct explain_msg *next;
    /** \brief Identifier. */
    unsigned int id;
    /** \brief Opsname alias for the identifier. */
    char opsName[EXPLAIN_MAX_OPS_NAME_LENGTH];
    /** \brief Destination symbol. */
    char dstSymbol[EXPLAIN_MAX_SYMBOL_LENGTH];
    /** \brief Source symbol. */
    char srcSymbol[EXPLAIN_MAX_SYMBOL_LENGTH];
    /** \brief Source endianness. */
    explain_endianess_t srcEndian;
    /** \brief Destination endianness. */
    explain_endianess_t dstEndian;
    /** \brief Linked list. */
    LIST_STRUCT(fields);
} explain_msg_t;


/** 
**  \brief A message linked list.
*/
typedef struct explain_msg_list
{
    /** \brief Linked list. */
    LIST_STRUCT(messages);
} explain_msg_list_t;


/************************************************************************/
/** \brief Perform any required initialization.
**
**  \par Description
**       This function initializes the outer message linked list.
**
**  \par Assumptions, External Events, and Notes:
**       This function must be called before any other API calls. 
**
**  \param [in]    handle  the handle to the message list.
**
*************************************************************************/
void explain_message_init(explain_msg_list_t *handle);


/************************************************************************/
/** \brief Perform any required cleanup.
**
**  \par Description
**       This cleans up all allocated memory.
**
**  \par Assumptions, External Events, and Notes:
**       This function must be called before application exit.
**
**  \param [in]    handle  the handle to the message list.
**
*************************************************************************/
void explain_message_deinit(explain_msg_list_t *handle);


/************************************************************************/
/** \brief Add a new message to the linked list.
**
**  \par Description
**       This function allocates, initializes, and adds a message to 
**       the messages linked list.
**
**  \par Assumptions, External Events, and Notes:
**       message_init must be called before a message can be added.
**
**  \returns msg_t the pointer to the new message on success, NULL on
**           failure.
**
**  \param [in]    handle  the handle to the message list.
**
*************************************************************************/
explain_msg_t *explain_message_add(explain_msg_list_t *handle);


/************************************************************************/
/** \brief Add a new field to a message.
**
**  \par Description
**       This function allocates a new field, copies the contents of 
**       addition to the new field, and adds the field to the message
**       fields linked list.
**
**  \par Assumptions, External Events, and Notes:
**       message_add must be called before a field can be added.
**
**  \param [in/out]   msg_ptr  The pointer to the message.
**                             
**  \param [in]       addition The pointer to the field to copy.
** 
**  \returns field_t the pointer to the new field on success, NULL on
**           failure.
**
*************************************************************************/
explain_field_t * explain_field_add(explain_msg_t *msg_ptr, const explain_field_t *addition);


/************************************************************************/
/** \brief Find a message via its id.
**
**  \par Description
**       This function searches the messages linked list for the id and
**       returns a pointer to message if found.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   id  The message id.
**
**  \param [in]   handle  The handle to the message list.
**
**  \returns msg_t the pointer to the message on success, NULL on
**           failure.
**
*************************************************************************/
explain_msg_t * explain_message_find_via_id(unsigned int id, explain_msg_list_t *handle);


/************************************************************************/
/** \brief Find a message via its ops name.
**
**  \par Description
**       This function searches the messages linked list for the ops
**       name and returns a pointer to message if found.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   ops_name a pointer to the ops name.
**
**  \param [in]   handle  The handle to the message list.
**
**  \returns msg_t the pointer to the message on success, NULL on
**           failure.
**
*************************************************************************/
explain_msg_t * explain_message_find_via_name(const char *ops_name, explain_msg_list_t *handle);


/************************************************************************/
/** \brief Find a message via its source symbol name.
**
**  \par Description
**       This function searches the messages linked list for the source
**       symbol name and returns a pointer to message if found.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   src_symbol a pointer to the source symbol.
**
**  \param [in]   handle  The handle to the message list.
**
**  \returns msg_t the pointer to the message on success, NULL on
**           failure.
**
*************************************************************************/
explain_msg_t * explain_message_find_via_src_symbol(const char *src_symbol, explain_msg_list_t *handle);


/************************************************************************/
/** \brief Find a message via its destination symbol name.
**
**  \par Description
**       This function searches the messages linked list for the
**       destination symbol name and returns a pointer to message if 
**       found.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   dst_symbol a pointer to the destination symbol.
**
**  \param [in]   handle  The handle to the message list.
**
**  \returns msg_t the pointer to the message on success, NULL on
**           failure.
**
*************************************************************************/
explain_msg_t * explain_message_find_via_dst_symbol(const char *dst_symbol, explain_msg_list_t *handle);


/************************************************************************/
/** \brief Print all messages and fields.
**
**  \par Description
**       This iterates through the linked list and prints all messages
**       and all fields.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   handle  The handle to the message list.
**
**
*************************************************************************/
void explain_print_all_fields(explain_msg_list_t *handle);


#ifdef __cplusplus
}
#endif 

#endif /* MESSAGE_H */
