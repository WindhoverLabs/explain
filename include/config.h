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
#ifndef CONFIG_H
#define CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <linux/limits.h>

/* Start for explain. */
/** \brief Maximum buffer size to store the json input string. */
#define EXPLAIN_MAX_BUFFER_SIZE             (10000)
/** \brief Maximum length of the input file path. */
#define EXPLAIN_MAX_PATH_LENGTH             PATH_MAX
/* Not yet used. */
/** \brief The endianness of the source. */
#define EXPLAIN_SRC_ENDIANNESS              (0)
/* End for explain. */

/* Start for message. */
/** \brief Maximum length of an ops name. */
#define EXPLAIN_MAX_OPS_NAME_LENGTH         (256)
/** \brief Maximum length of a symbol name. */
#define EXPLAIN_MAX_SYMBOL_LENGTH           (256)
/* End for messages. */

/* Start for parser. */
/* keys used in input json. */
/** \brief Key name for message id. */
#define EXPLAIN_IDENTIFICATION_KEY          "id"
/** \brief Key name for the destination symbol. */
#define EXPLAIN_DESTINATION_SYMBOL          "dst_symbol"
/** \brief Key name for the source symbol. */
#define EXPLAIN_SOURCE_SYMBOL               "src_symbol"
/** \brief Key name for message ops name. */
#define EXPLAIN_OPS_MESSAGE_NAME_KEY        "ops_name"
/** \brief Key name for message op name. */
#define EXPLAIN_OPS_FIELD_NAME_KEY          "op_name"
/** \brief Key name for source endianness. */
#define EXPLAIN_SOURCE_ENDIANNESS_KEY       "src_endian"
/** \brief Key name for destination endianness. */
#define EXPLAIN_DEST_ENDIANNESS_KEY         "dst_endian"
/** \brief Key name for length. */
#define EXPLAIN_LENGTH_KEY                  "length"
/** \brief Key name for source offset. */
#define EXPLAIN_SOURCE_OFFSET_KEY           "src_offset"
/** \brief Key name for destination offset. */
#define EXPLAIN_DESTINATION_OFFSET_KEY      "dst_offset"
/* Value definitions. */
/** \brief Max length of endianness key. */
#define EXPLAIN_MAX_ENDIANNESS_LENGTH       (1)
/** \brief Little endian value. */
#define EXPLAIN_LITTLE_ENDIAN_VALUE         "L"
/** \brief Big endian value. */
#define EXPLAIN_BIG_ENDIAN_VALUE            "B"
/** \brief Max key length. */
#define EXPLAIN_MAX_KEY_LENGTH              (24)
/* Max recursive calls for the parser. */
/** \brief Max recursive call count for json parser. */
#define EXPLAIN_MAX_RECURSIVE_CALL_COUNT    (100)
/* End for parser. */


#ifdef __cplusplus
}
#endif 

#endif /* CONFIG_H */
