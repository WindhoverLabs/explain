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
#include "parser.h"
#include <string.h>
#include <stdio.h>


bool json_parse(json_object * jobj, unsigned int *call_count, explain_data_t *handle) 
{
    enum json_type type = 0;
    bool returnBool = false;

    /* Null pointer check */
    if(0 == jobj || 0 == call_count)
    {
        goto end_of_function;
    }

    /* Recursive call stack depth check */
    if (*call_count >= MAX_RECURSIVE_CALL_COUNT)
    {
        printf("Recursive call stack exceeded %d\n", *call_count);
        goto end_of_function;
    }
    else
    {
        *call_count = *call_count + 1;
    }

    json_object_object_foreach(jobj, key, val) 
    {
        type = json_object_get_type(val);

        switch (type) 
        {
            case json_type_boolean: 
            {
                printf("Unknown json type boolean in parser\n");
                break;
            }
            case json_type_double: 
            {
                printf("Unknown json type double in parser\n");
                break;
            }
            case json_type_int: 
            {
                returnBool = parse_json_value(val, key, handle);
                break; 
            }
            case json_type_string:
            {
                returnBool = parse_json_value(val, key, handle);
                break; 
            }
            case json_type_object: 
            {
                printf("Unknown json type object in parser\n");
                //jobj = json_object_object_get(jobj, key);
                //json_parse(jobj, state, cursor); 
                break;
            }
            case json_type_array: 
            {
                //printf("json_type_array\n");
                returnBool = json_parse_array(jobj, key, call_count, handle);
                break;
            }
            default :
            {
                printf("Unkown json type in parser\n");
            }
        }
    }

end_of_function:
    return (returnBool);
} 


bool json_parse_array(json_object *jobj, const char *key, unsigned int *call_count, explain_data_t *handle) 
{
    unsigned int i      = 0;
    enum json_type type = 0;
    bool returnBool  = false;

    /* Null pointer check */
    if(0 == jobj || 0 == key || 0 == call_count)
    {
        goto end_of_function;
    }

    /* Recursive call stack depth check */
    if (*call_count >= MAX_RECURSIVE_CALL_COUNT)
    {
        printf("Recursive call stack exceeded in array %d\n", *call_count);
        goto end_of_function;
    }
    else
    {
        *call_count = *call_count + 1;
    }

    json_object *jarray = jobj; 

    /* Simply get the array. */
    if(key) 
    {
        /* Getting the array if it is a key value pair. */
        jarray = json_object_object_get(jobj, key); 
    }

    /* Getting the length of the array. */
    int arraylen = json_object_array_length(jarray); 
    //printf("Array Length: %d\n", arraylen);

    json_object * jvalue;

    for (i = 0; i < arraylen; ++i)
    {
        /* Getting the array element at position i */
        jvalue = json_object_array_get_idx(jarray, i); 
        type = json_object_get_type(jvalue);

        if (type == json_type_array) 
        {
            returnBool = json_parse_array(jvalue, NULL, call_count, handle);
        }
        else if (type != json_type_object) 
        {
            parse_json_value(jvalue, key, handle);
        }
        else 
        {
            returnBool = json_parse(jvalue, call_count, handle);
        }
    }

end_of_function:
    return (returnBool);
}


bool parse_json_value(json_object *jobj, const char* key, explain_data_t *handle)
{
    enum json_type type = 0;
    bool returnBool  = false;

    /* Null pointer check */
    if(0 == jobj || 0 == key)
    {
        goto end_of_function;
    }

    /* Getting the type of the json object */
    type = json_object_get_type(jobj); 
    switch (type) 
    {
        case json_type_boolean: 
        {
            printf("Unknown json type boolean in parser\n");
            break;
        }
        case json_type_double: 
        {
            printf("Unknown json type double in parser\n");
            break;
        }
        case json_type_int: 
        {
            returnBool = load_int(jobj, key, handle);
            break;
        }
        case json_type_string: 
        {
            returnBool = load_string(jobj, key, handle);
            break;
        }
        default :
        {
            printf("Unkown json type value in parser\n");
        }
    }

end_of_function:
    return (returnBool);
}


bool load_int(json_object * jobj, const char *key, explain_data_t *handle)
{
    bool returnBool = false;
    int value = json_object_get_int(jobj);

    /* Null pointer check */
    if(0 == jobj || 0 == key)
    {
        goto end_of_function;
    }

    if (0 == strncmp(key, LENGTH_KEY, MAX_KEY_LENGTH))
    {
        //printf("got key fields length %d\n", value);
        handle->currentField.length = value;
        returnBool = true;
    }
    else if (0 == strncmp(key, SOURCE_OFFSET_KEY, MAX_KEY_LENGTH))
    {
        //printf("got key fields source %d\n", value);
        handle->currentField.srcOffset = value;
        returnBool = true;
    }
    else if (0 == strncmp(key, DESTINATION_OFFSET_KEY, MAX_KEY_LENGTH))
    {
        //printf("got key fields destination %d\n", value);
        handle->currentField.dstOffset = value;
        /* For now assume a field is complete. */
        /* TODO error checking. */
        (void) explain_field_add(handle->currentMsg, &handle->currentField);
        returnBool = true;
    }
    else
    {
        /* Error state */
        printf("got unknown key in load_int %s\n", key);

    }

end_of_function:
    return (returnBool);
}


bool load_string(json_object * jobj, const char *key, explain_data_t *handle)
{
    bool returnBool = FALSE;
    const char  *value = json_object_get_string(jobj);

    /* Null pointer check */
    if(0 == jobj || 0 == key)
    {
        goto end_of_function;
    }

    /* Check keys for known values */
    if (0 == strncmp(key, IDENTIFICATION_KEY, MAX_KEY_LENGTH))
    {
        handle->currentMsg->id = strtoul(value, NULL, 16);
        //printf("got key bitmap id %d\n", handle->currentMsg->id);
        returnBool = true;
    }
    else if (0 == strncmp(key, DESTINATION_SYMBOL, MAX_KEY_LENGTH))
    {
        strncpy(handle->currentMsg->dstSymbol, value, EXPLAIN_MAX_OPS_NAME_LENGTH);
        //printf("got key bitmap dest symbol %s\n", handle->currentMsg->opsName);
        returnBool = true;
    }
    else if (0 == strncmp(key, SOURCE_SYMBOL, MAX_KEY_LENGTH))
    {
        strncpy(handle->currentMsg->srcSymbol, value, EXPLAIN_MAX_OPS_NAME_LENGTH);
        //printf("got key bitmap src symbol %s\n", handle->currentMsg->opsName);
        returnBool = true;
    }
    else if (0 == strncmp(key, OPS_MESSAGE_NAME_KEY, MAX_KEY_LENGTH))
    {
        strncpy(handle->currentMsg->opsName, value, EXPLAIN_MAX_OPS_NAME_LENGTH);
        //printf("got key bitmap ops_name %s\n", handle->currentMsg->opsName);
        returnBool = true;
    }
    else if (0 == strncmp(key, OPS_FIELD_NAME_KEY, MAX_KEY_LENGTH))
    {
        strncpy(handle->currentField.opName, value, EXPLAIN_MAX_OPS_NAME_LENGTH);
        //printf("got key field op_name %s\n", handle->currentField.opName);
        returnBool = true;
    }
    else if (0 == strncmp(key, SOURCE_ENDIANNESS_KEY, MAX_KEY_LENGTH))
    {
        /* Decode endianess. */
        if(0 == strncmp(value, LITTLE_ENDIAN_VALUE, MAX_ENDIANNESS_LENGTH))
        {
            handle->currentMsg->srcEndian = EXPLAIN_LITTLE_ENDIAN;
            returnBool = true;
        }
        else if (0 == strncmp(value, BIG_ENDIAN_VALUE, MAX_ENDIANNESS_LENGTH))
        {
            handle->currentMsg->srcEndian = EXPLAIN_BIG_ENDIAN;
            returnBool = true;
        }
        else
        {
            /* TODO error condition unknown endianness value. */
            printf("Unknown endianness value in parser, got %s\n", value);
        }
        //printf("got key field src endian %d\n", app_data.currentMsg->srcEndian);
    }
    else if (0 == strncmp(key, DEST_ENDIANNESS_KEY, MAX_KEY_LENGTH))
    {
        /* Decode endianness. */
        if(0 == strncmp(value, LITTLE_ENDIAN_VALUE, MAX_ENDIANNESS_LENGTH))
        {
            handle->currentMsg->dstEndian = EXPLAIN_LITTLE_ENDIAN;
            returnBool = true;
        }
        else if (0 == strncmp(value, BIG_ENDIAN_VALUE, MAX_ENDIANNESS_LENGTH))
        {
            handle->currentMsg->dstEndian = EXPLAIN_BIG_ENDIAN;
            returnBool = true;
        }
        else
        {
            /* TODO error condition unknown endianness value. */
            printf("Unknown endianness value in parser, got %s\n", value);
        }
        //printf("got key field dst endian %d\n", app_data.currentMsg->dstEndian);
        /* For now assume we've completed a message. */
        /* Add a new message. */
        handle->currentMsg = explain_message_add(&handle->message_list);
    }
    else
    {
        /* Error state */
        printf("got unknown key in load_string %s\n", key);
    }

end_of_function:
    return (returnBool);
}



