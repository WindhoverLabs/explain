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
#ifndef UTILS_H
#define UTILS_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

/************************************************************************/
/** \brief Validate an input file path.
**
**  \par Description
**       This attempts to validate the path to an input file.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   inputPath  The input path.
** 
**  \returns TRUE for success, FALSE for failure.
**
*************************************************************************/
bool validate_path(const char *inputPath);


/************************************************************************/
/** \brief Copy the input from filepath to fileContent.
**
**  \par Description
**       Opens and copies the file indicated by the file path to the 
**       buffer fileContent.
**
**  \par Assumptions, External Events, and Notes:
**       fileContent must be large enough to store the contents of the
**       file indicated by filepath.
**
**  \param [in]   filePath  The input file path.
** 
**  \param [in/out]   fileContent  The buffer to copy to.
**
**  \returns TRUE for success, FALSE for failure.
**
*************************************************************************/
bool read_input(const char *filePath, char *fileContent);


/************************************************************************/
/** \brief Get the ccsds message id from a buffer.
**
**  \par Description
**       Get the ccsds message id of a message stored in the input 
**       buffer.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in]   input  The input buffer.
**
**  \returns the message id.
**
*************************************************************************/
unsigned int get_ccsds_msg_id(const char *input);


#ifdef __cplusplus
}
#endif 

#endif /* UTILS_H */
