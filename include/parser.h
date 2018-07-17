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
#ifndef PARSER_H
#define PARSER_H

#ifdef __cplusplus
extern "C" {
#endif

#include "explain.h"
#include "config.h"
#include <json/json.h>
#include <stdbool.h>

/* keys used in input json. */
/** \brief Key name for message id. */
#define IDENTIFICATION_KEY          EXPLAIN_IDENTIFICATION_KEY
/** \brief Key name for the destination symbol. */
#define DESTINATION_SYMBOL          EXPLAIN_DESTINATION_SYMBOL
/** \brief Key name for the source symbol. */
#define SOURCE_SYMBOL               EXPLAIN_SOURCE_SYMBOL
/** \brief Key name for message ops name. */
#define OPS_MESSAGE_NAME_KEY        EXPLAIN_OPS_MESSAGE_NAME_KEY
/** \brief Key name for message op name. */
#define OPS_FIELD_NAME_KEY          EXPLAIN_OPS_FIELD_NAME_KEY
/** \brief Key name for source endianness. */
#define SOURCE_ENDIANNESS_KEY       EXPLAIN_SOURCE_ENDIANNESS_KEY
/** \brief Key name for destination endianness. */
#define DEST_ENDIANNESS_KEY         EXPLAIN_DEST_ENDIANNESS_KEY
/** \brief Key name for length. */
#define LENGTH_KEY                  EXPLAIN_LENGTH_KEY
/** \brief Key name for source offset. */
#define SOURCE_OFFSET_KEY           EXPLAIN_SOURCE_OFFSET_KEY
/** \brief Key name for destination offset. */
#define DESTINATION_OFFSET_KEY      EXPLAIN_DESTINATION_OFFSET_KEY
/* Value definitions. */
/** \brief Max length of endianness key. */
#define MAX_ENDIANNESS_LENGTH       EXPLAIN_MAX_ENDIANNESS_LENGTH
/** \brief Little endian value. */
#define LITTLE_ENDIAN_VALUE         EXPLAIN_LITTLE_ENDIAN_VALUE
/** \brief Big endian value. */
#define BIG_ENDIAN_VALUE            EXPLAIN_BIG_ENDIAN_VALUE
/** \brief Max key length. */
#define MAX_KEY_LENGTH              EXPLAIN_MAX_KEY_LENGTH
/* Max recursive calls for the parser. */
/** \brief Max recursive call count for json parser. */
#define MAX_RECURSIVE_CALL_COUNT    EXPLAIN_MAX_RECURSIVE_CALL_COUNT


/************************************************************************/
/** \brief Parses a json object and loads the linked list of the 
**         explain data handle.
**
**  \par Description
**       This function parses the json object and loads the messages
**       linked list pointed to by the explain data handle.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]        jobj  The json object.
**
**  \param [in\out]    call_count  The call_count to limit recursion.
**
**  \param [in\out]    handle  The handle to the explain data structure.
**
**  \returns true for success, false for failure.
**
*************************************************************************/
bool json_parse(json_object * jobj, unsigned int *call_count, explain_data_t *handle);


/************************************************************************/
/** \brief Parses a value in a json key value pair.
**
**  \par Description
**       This function parses a value in a key value pair and calls the
**       appropriate function to continue parsing depending on the type. 
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]        jobj    The json object.
**                             
**  \param [in]        key     The current key.
**
**  \param [in\out]    handle  The handle to the explain data structure.
**
**  \returns true for success, false for failure.
**
*************************************************************************/
bool parse_json_value(json_object *jobj, const char* key, explain_data_t *handle);


/************************************************************************/
/** \brief Parses a json array object and loads the linked list of the 
**         explain data handle.
**
**  \par Description
**       This function parses a json array object and loads the messages
**       linked list pointed to by the explain data handle.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]        jobj  The json object.
**
**  \param [in]        key     The current key.
**
**  \param [in\out]    call_count  The call_count to limit recursion.
**
**  \param [in\out]    handle  The handle to the explain data structure.
**
**  \returns true for success, false for failure.
**
*************************************************************************/
bool json_parse_array(json_object *jobj, const char *key, unsigned int *call_count, explain_data_t *handle);


/************************************************************************/
/** \brief Parse and load an int value into the current message field.
**
**  \par Description
**       This function parses and loads a integer into the current
**       message or message field pointed to by the handle.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]        jobj    The json object.
**                             
**  \param [in]        key     The current key.
**
**  \param [in\out]    handle  The handle to the explain data structure.
**
**  \returns true for success, false for failure.
**
*************************************************************************/
bool load_int(json_object * jobj, const char *key, explain_data_t *handle);


/************************************************************************/
/** \brief Parse and load a string value into the current message field.
**
**  \par Description
**       This function parses and loads a string into the current
**       message or message field pointed to by the handle.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]        jobj    The json object.
**                             
**  \param [in]        key     The current key.
**
**  \param [in\out]    handle  The handle to the explain data structure.
**
**  \returns true for success, false for failure.
**
*************************************************************************/
bool load_string(json_object * jobj, const char *key, explain_data_t *handle);


#ifdef __cplusplus
}
#endif 

#endif /* PARSER_H */
