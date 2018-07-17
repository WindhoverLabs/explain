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
#ifndef MEMTOOLS_H
#define MEMTOOLS_H

#ifdef __cplusplus
extern "C" {
#endif

/************************************************************************/
/** \brief An extended memcpy with support for bits.
**
**  \par Description
**       This function performs a bitwise memcpy.
**
**  \par Assumptions, External Events, and Notes:
**       The total destination buffer must be cleared before repeated
**       calls to this function to copy fields are made.
**
**  \param [in/out]    dst_buf    The destination buffer.
**
**  \param [in]        dst_off    The destination offset.
**
**  \param [in]        src_buf    The source buffer.
**
**  \param [in]        src_off    The source offset.
**
**  \param [in]        bit_len    The bit length to copy.
**
*************************************************************************/
void memcpy_bitwise(char *dst_buf, unsigned int dst_off, const char *src_buf, unsigned int src_off, unsigned int bit_len);


#ifdef __cplusplus
}
#endif 

#endif /* MEMTOOLS_H */
