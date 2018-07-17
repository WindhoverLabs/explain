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
#include "cfe_sb.h"
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include "utils.h"


bool validate_path(const char *inputPath)
{
    struct stat fileStat;
    bool returnBool = false;
    int returnVal = -1;

    returnVal = stat(inputPath, &fileStat);

    if (returnVal < 0)
    {
        goto end_of_function;
    }
    else
    {
        returnBool = true;
    }

    /* TODO add additional validation */

end_of_function:
    return returnBool;
}


bool read_input(const char* filePath, char* fileContent)
{
    FILE *f   = 0;
    char c    = 0;
    int index = 0;
    boolean returnBool = true;
    
    f = fopen(filePath, "rt");
    if (NULL == f)
    {
        printf("fopen returned errno %d\n", errno);
        returnBool = false;
        goto end_of_function;
    }
    
    while((c = fgetc(f)) != EOF)
    {
        fileContent[index] = c;
        index++;
    }

    fileContent[index] = '\0';

end_of_function:
    return returnBool;
}


unsigned int get_ccsds_msg_id(const char *input)
{
    CFE_SB_Msg_t*   MsgPtr  = (CFE_SB_MsgPtr_t) input;
    unsigned int id = 0;

    /* Null pointer checks */
    if (0 == input)
    {
        goto end_of_function;
    }

    /* Get the CCSDS message id */
    id = CFE_SB_GetMsgId(MsgPtr);

end_of_function:
    return id;
}
