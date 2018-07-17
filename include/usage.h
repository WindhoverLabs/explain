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
#ifndef USAGE_H
#define USAGE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <getopt.h>
#include <stdbool.h>

/** 
**  \brief application short options.
*/
typedef enum 
{
    /** \brief short help option -h */
    OPT_HELP = 'h',
    /** \brief short path option -p */
    OPT_PATH = 'p'
} explain_options_t;



/************************************************************************/
/** \brief Print a usage message and exit.
**
**  \par Description
**       This function prints a usage calls and exits the application.
**
**  \par Assumptions, External Events, and Notes:
**       For use with a stand-alone application that parses user
**       arguments.
**
*************************************************************************/
void usage(void);


/************************************************************************/
/** \brief Parse input argument options.
**
**  \par Description
**       This function parses arguments and copies the input file path
**       if provided.
**
**  \par Assumptions, External Events, and Notes:
**       None.
**
**  \param [in/out]   inputPath    A pointer to copy the input path to.
**                             
**  \param [in]       argc    The argument count.
**
**  \param [in]       argv    The argument vector.
** 
**  \returns bool true for success, false for failure.
**
*************************************************************************/
bool parse_options(char *inputPath, int argc, char **argv);


#ifdef __cplusplus
}
#endif 

#endif /* USAGE_H */
