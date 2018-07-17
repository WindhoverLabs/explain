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
#ifndef EXPLAIN_H
#define EXPLAIN_H

#ifdef __cplusplus
extern "C" {
#endif

#include "message.h"
#include "config.h"
#include <stdbool.h>


/** 
**  \brief Application data.
*/
typedef struct 
{
    /** \brief Path to the input json file. */
    char inputPath[EXPLAIN_MAX_PATH_LENGTH];
    /** \brief The raw json string from the input file. */
    char rawInput[EXPLAIN_MAX_BUFFER_SIZE];
    /** \brief The current message being parsed. */
    explain_msg_t *currentMsg;
    /** \brief The current field being parsed. */
    explain_field_t currentField;
    /** \brief The message linked list. */
    explain_msg_list_t message_list;
} explain_data_t;


/** 
**  \brief Bitwise copy direction enumeration.
*/
typedef enum
{
    /** \brief Copy from source to destination. */
    EXPLAIN_FORWARD = 0,
    /** \brief Copy from destination to source. */
    EXPLAIN_REVERSE = 1
} explain_direction_t;


/************************************************************************/
/** \brief Initialize explain library data.
**
**  \par Description
**       This function clears the data structure, initializes the
**       linked list, and allocates the first message.
**
**  \par Assumptions, External Events, and Notes:
**       This function must be called first.
**
**  \param [in/out]    app_data    The pointer to the app_data to init.
** 
**  \returns true for success, false for failure.
**
*************************************************************************/
bool explain_init_data(explain_data_t *app_data);

/************************************************************************/
/** \brief Uninitialize explain library data.
**
**  \par Description
**       This deallocates any allocated memory.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in/out]    app_data    The pointer to explain library data.
**
*************************************************************************/
void explain_uninit_data(explain_data_t *app_data);

/************************************************************************/
/** \brief Load the memory map from json.
**
**  \par Description
**       This function parses a memory map stored in a json file and 
**       stores in a linked list pointed to by the explain handle.
**
**  \par Assumptions, External Events, and Notes:
**       init_data must be called first to initialize explain data.
**
**  \param [in]        filepath       Path to the json input file.
**
**  \param [in\out]    handle         The handle to explain data.
**
**  \returns true for success, false for failure.
**
*************************************************************************/
bool explain_load_memory_map(const char *filepath, explain_data_t *handle);


/************************************************************************/
/** \brief Translate a buffer between source and destination ABI.
**
**  \par Description
**       This function translates the application binary interface of
**       a source to a destination. The memory copy will not exceed
**       max length. If a field exceeds max length the field will not
**       be copied. The destination buffer will be memset before the
**       translation starts.
**
**  \par Assumptions, External Events, and Notes:
**       The returned size written may be shorter than sizeof the 
**       structure due to padding at the end of the structure.
**
**
**  \param [in\out]    dst    The destination buffer.
**
**  \param [in]        src    The source buffer.
**
**  \param [in]        definition    The handle to the message 
**                                   definition.
**  \param [in]        max_len       The max byte length to copy. 
**
**  \param [in]        direction     The direction of translation.
**
**  \returns size written in bytes for success -1 for failure and sets
**           an appropriete error number.
**
*************************************************************************/
int explain_translate_buffer(char *dst, const char *src, const explain_msg_t *definition, unsigned int max_len, explain_direction_t direction);


#ifdef __cplusplus
}
#endif 

#endif /* EXPLAIN_H */
