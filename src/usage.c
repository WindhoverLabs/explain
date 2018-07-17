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
#include <getopt.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "config.h"
#include "usage.h"


/* Application long options. */
static struct option longopts[] = 
{
    /* Long help option -help. */
    {"help", no_argument, NULL, OPT_HELP},
    /* Long path option -path. */
    {"path", required_argument, NULL, OPT_PATH},
    /* Null. */
    {0, 0, 0, 0}
};


void usage(void)
{
  printf("explain 0.0.0 requires a json file path argument\n");
  printf("Parameters with '=' requires an argument\n");
  printf("[ Example ]\n");
  printf("  ./explain -p input.json\n");
  printf("[ Options ]\n");
  printf("  --path=        : Specify the json input file\n");
  printf("  --help         : Print this help\n");
  exit(EXIT_SUCCESS);
}


bool parse_options(char *inputPath, int argc, char **argv)
{
    int ch = 0;
    bool returnBool = false;

    assert(inputPath);

    /* make -p input.json required */
    if (argc == 1)
    {
        usage();
        goto end_of_function;
    }

    while ((ch = getopt_long(argc, argv, "hp:", longopts, NULL)) != -1) 
    {
        switch(ch) 
        {
            case OPT_HELP:
            {
                usage();
                break;
            }
            case OPT_PATH:
            {
                (void) strncpy(inputPath, optarg, EXPLAIN_MAX_PATH_LENGTH);
                returnBool = true;
                break;
            }
            default:
            {
                usage();
                break;
            }
        }
    }

end_of_function:

    return returnBool;
}

