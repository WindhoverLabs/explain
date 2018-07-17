/******************************************************************************
** File: cfe_sb.h
**
**      Copyright (c) 2004-2006, United States government as represented by the
**      administrator of the National Aeronautics Space Administration.
**      All rights reserved. This software(cFE) was created at NASA's Goddard
**      Space Flight Center pursuant to government contracts.
**
**      This is governed by the NASA Open Source Agreement and may be used,
**      distributed and modified only pursuant to the terms of that agreement.
**
**
** Purpose:
**      This header file contains all definitions for the cFE Software Bus
**      Application Programmer's Interface.
**
** Author:   R.McGraw/SSI
**
** $Log: cfe_sb.h  $
** Revision 1.10 2011/04/07 08:34:14GMT-05:00 lwalling 
** This file references CFE TIME structures, therefore it should include cfe_time.h
** Revision 1.9 2009/07/29 19:21:50EDT aschoeni 
** Added ZeroCopyHandle_t
** Revision 1.8 2009/07/24 18:25:20EDT aschoeni 
** Added Zero Copy Mode
** Revision 1.7 2009/07/17 19:42:20EDT aschoeni 
** Added PassMsg API to sb to support sequence count preservation
** Revision 1.6 2009/06/10 09:15:06EDT acudmore 
** updated os_bsp.h to cfe_psp.h
** Revision 1.5 2009/04/29 10:03:59EDT rmcgraw 
** DCR5801:11 Changed comments related to subscription return value
** Revision 1.4 2009/02/27 09:55:04EST rmcgraw 
** DCR1709:1 Removed incorrect comment in SetTotalMsgLength 
** and reworded other comments
** Revision 1.3 2009/02/26 17:49:19EST rmcgraw 
** DCR6805:1 Added note under subscription API declaration
** Revision 1.2 2008/12/08 12:06:56EST dkobe 
** Updates to correct doxygen errors
** Revision 1.1 2008/04/17 08:05:22EDT ruperera 
** Initial revision
** Member added to cfe project on tlserver3
** Revision 1.25 2007/09/25 10:34:38EDT rjmcgraw 
** DCR5127 Added doxygen comments
** Revision 1.24 2007/07/06 13:18:35EDT rjmcgraw 
** DCR469:1 Changed function prototype for GetLastSenderId
** Revision 1.23 2007/05/23 11:22:02EDT dlkobe 
** Added doxygen formatting
** Revision 1.22 2007/04/19 15:47:03EDT rjmcgraw 
** Moved subscription reporting structs to cfe_sb_msg.h
** Revision 1.20 2007/03/22 12:55:20EST rjmcgraw 
** Added comments regarding Qos
** Revision 1.19 2007/01/24 16:49:35EST rjmcgraw
** Added Pipe to SubEntries_t
** Revision 1.18 2007/01/08 14:42:18EST rjmcgraw
** Moved SubscribeLocal prototypes to this file from cfe_sb_priv.h
** Revision 1.17 2007/01/04 14:49:44EST rjmcgraw
** Added SubType to CFE_SB_SubRprtMsg_t
** Revision 1.16 2007/01/02 10:01:35EST rjmcgraw
** Moved structs from priv.h to cfe_sb.h for exposure to apps
** Revision 1.15 2006/12/28 16:27:34EST rjmcgraw
** Added cmd codes for SB subscription processing
**
******************************************************************************/

#ifndef _cfe_sb_
#define _cfe_sb_

/*
** Includes
*/

#include "common_types.h"
#include "cfe_mission_cfg.h"
#include "ccsds.h"


/*
** Macro Definitions
*/
#define CFE_BIT(x)   (1 << (x))               /**< \brief Places a one at bit positions 0 - 31*/
#define CFE_SET(i,x) ((i) |= CFE_BIT(x))      /**< \brief Sets bit x of i */
#define CFE_CLR(i,x) ((i) &= ~CFE_BIT(x))     /**< \brief Clears bit x of i */
#define CFE_TST(i,x) (((i) & CFE_BIT(x)) != 0)/**< \brief TRUE(non zero) if bit x of i is set */


/*
** Type Definitions
*/

/**< \brief Generic Software Bus Message Type Definition */
typedef union {
    CCSDS_PriHdr_t      Hdr;   /**< \brief CCSDS Primary Header #CCSDS_PriHdr_t */
    uint32              Dword; /**< \brief Forces minimum of 32-bit alignment for this object */
    uint8               Byte[sizeof(CCSDS_PriHdr_t)];   /**< \brief Allows byte-level access */
}CFE_SB_Msg_t;

/**< \brief Generic Software Bus Command Header Type Definition */
typedef struct{
    CCSDS_PriHdr_t      Pri;/**< \brief CCSDS Primary Header #CCSDS_PriHdr_t */
    CCSDS_CmdSecHdr_t   Sec;/**< \brief CCSDS Command Secondary Header #CCSDS_CmdSecHdr_t */
}CFE_SB_CmdHdr_t;

/**< \brief Generic Software Bus Telemetry Header Type Definition */
typedef struct{
    CCSDS_PriHdr_t      Pri;/**< \brief CCSDS Primary Header #CCSDS_PriHdr_t */
    CCSDS_TlmSecHdr_t   Sec;/**< \brief CCSDS Telemetry Secondary Header #CCSDS_TlmSecHdr_t */
}CFE_SB_TlmHdr_t;

#define CFE_SB_CMD_HDR_SIZE     (sizeof(CFE_SB_CmdHdr_t))/**< \brief Size of #CFE_SB_CmdHdr_t in bytes */
#define CFE_SB_TLM_HDR_SIZE     (sizeof(CFE_SB_TlmHdr_t))/**< \brief Size of #CFE_SB_TlmHdr_t in bytes */



/**< \brief  CFE_SB_MsgId_t to primitive type definition 
** 
** Software Bus message identifier used in many SB APIs
*/
typedef uint16 CFE_SB_MsgId_t;

/**< \brief  CFE_SB_MsgPtr_t defined as a pointer to an SB Message */
typedef CFE_SB_Msg_t *CFE_SB_MsgPtr_t;

/**< \brief  CFE_SB_MsgPayloadPtr_t defined as an opaque pointer to a message Payload portion */
typedef uint8 *CFE_SB_MsgPayloadPtr_t;


/*
**  cFE SB Application Programmer Interface's (API's)
*/


/*****************************************************************************/
/** 
** \brief Initialize a buffer for a software bus message.
**
** \par Description
**          This routine fills in the header information needed to create a 
**          valid software bus message.
**
** \par Assumptions, External Events, and Notes:
**          None  
**
** \param[in]  MsgPtr  A pointer to the buffer that will contain the message.  
**                     This will point to the first byte of the message header.  
**                     The \c void* data type allows the calling routine to use
**                     any data type when declaring its message buffer. 
**
** \param[in]  MsgId   The message ID to put in the message header.
**
** \param[in]  Length  The total number of bytes of message data, including the SB 
**                     message header  .
**
** \param[in]  Clear   A flag indicating whether to clear the rest of the message:
**                     \arg TRUE - fill sequence count and packet data with zeroes.
**                     \arg FALSE - leave sequence count and packet data unchanged.
**
** \sa #CFE_SB_SetMsgId, #CFE_SB_SetUserDataLength, #CFE_SB_SetTotalMsgLength,
**     #CFE_SB_SetMsgTime, #CFE_SB_TimeStampMsg, #CFE_SB_SetCmdCode 
**/
void CFE_SB_InitMsg(void           *MsgPtr,
                    CFE_SB_MsgId_t MsgId,
                    uint16         Length,
                    boolean        Clear );

/*****************************************************************************/
/** 
** \brief Get the size of a software bus message header.
**
** \par Description
**          This routine returns the number of bytes in a software bus message header.  
**          This can be used for sizing buffers that need to store SB messages.  SB 
**          message header formats can be different for each deployment of the cFE.  
**          So, applications should use this function and avoid hard coding their buffer 
**          sizes.
**
** \par Assumptions, External Events, and Notes:
**          - For statically defined messages, a function call will not work.  The 
**            macros #CFE_SB_CMD_HDR_SIZE and #CFE_SB_TLM_HDR_SIZE are available for use 
**            in static message buffer sizing or structure definitions.  
**
** \param[in]  MsgId   The message ID to calculate header size for.  The size of the message 
**                     header may depend on the MsgId in some implementations.  For example, 
**                     if SB messages are implemented as CCSDS packets, the size of the header 
**                     is different for command vs. telemetry packets.
**
** \returns
** \retstmt The number of bytes in the software bus message header for 
**          messages with the given \c MsgId. endstmt
** \endreturns
**
** \sa #CFE_SB_GetUserData, #CFE_SB_GetMsgId, #CFE_SB_GetUserDataLength, #CFE_SB_GetTotalMsgLength,
**     #CFE_SB_GetMsgTime, #CFE_SB_GetCmdCode, #CFE_SB_GetChecksum 
**/
uint16 CFE_SB_MsgHdrSize(CFE_SB_MsgId_t MsgId);

/*****************************************************************************/
/** 
** \brief Get a pointer to the user data portion of a software bus message.
**
** \par Description
**          This routine returns a pointer to the user data portion of a software 
**          bus message.  SB message header formats can be different for each 
**          deployment of the cFE.  So, applications should use this function and 
**          avoid hard coding offsets into their SB message buffers.
**
** \par Assumptions, External Events, and Notes:
**          None  
**
** \param[in]  MsgPtr  A pointer to the buffer that contains the software bus message.
**
** \returns
** \retstmt A pointer to the first byte of user data within the software bus message. \endstmt
** \endreturns
**
** \sa #CFE_SB_GetMsgId, #CFE_SB_GetUserDataLength, #CFE_SB_GetTotalMsgLength,
**     #CFE_SB_GetMsgTime, #CFE_SB_GetCmdCode, #CFE_SB_GetChecksum, #CFE_SB_MsgHdrSize 
**/
void *CFE_SB_GetUserData(CFE_SB_MsgPtr_t MsgPtr);

/*****************************************************************************/
/** 
** \brief Get the message ID of a software bus message.
**
** \par Description
**          This routine returns the message ID from a software bus message.
**
** \par Assumptions, External Events, and Notes:
**          None  
**
** \param[in]  MsgPtr  A pointer to the buffer that contains the software bus message.
**
** \returns
** \retstmt The software bus Message ID from the message header. \endstmt
** \endreturns
**
** \sa #CFE_SB_GetUserData, #CFE_SB_SetMsgId, #CFE_SB_GetUserDataLength, #CFE_SB_GetTotalMsgLength,
**     #CFE_SB_GetMsgTime, #CFE_SB_GetCmdCode, #CFE_SB_GetChecksum, #CFE_SB_MsgHdrSize 
**/
CFE_SB_MsgId_t CFE_SB_GetMsgId(CFE_SB_MsgPtr_t MsgPtr);

/*****************************************************************************/
/** 
** \brief Sets the message ID of a software bus message.
**
** \par Description
**          This routine sets the Message ID in a software bus message header.
**
** \par Assumptions, External Events, and Notes:
**          None  
**
** \param[in]  MsgPtr  A pointer to the buffer that contains the software bus message.
**                     This must point to the first byte of the message header.
**
** \param[in]  MsgId   The message ID to put into the message header. 
**
** \returns
** \retstmt The software bus Message ID from the message header. \endstmt
** \endreturns
**
** \sa #CFE_SB_GetMsgId, #CFE_SB_SetUserDataLength, #CFE_SB_SetTotalMsgLength,
**     #CFE_SB_SetMsgTime, #CFE_SB_TimeStampMsg, #CFE_SB_SetCmdCode, #CFE_SB_InitMsg 
**/
void CFE_SB_SetMsgId(CFE_SB_MsgPtr_t MsgPtr,
                     CFE_SB_MsgId_t MsgId);

/*****************************************************************************/
/** 
** \brief Gets the length of user data in a software bus message.
**
** \par Description
**          This routine returns the size of the user data in a software bus message.
**
** \par Assumptions, External Events, and Notes:
**          None  
**
** \param[in]  MsgPtr  A pointer to the buffer that contains the software bus message.
**                     This must point to the first byte of the message header. 
**
** \returns
** \retstmt The size (in bytes) of the user data in the software bus message. \endstmt
** \endreturns
**
** \sa #CFE_SB_GetUserData, #CFE_SB_GetMsgId, #CFE_SB_SetUserDataLength, #CFE_SB_GetTotalMsgLength,
**     #CFE_SB_GetMsgTime, #CFE_SB_GetCmdCode, #CFE_SB_GetChecksum, #CFE_SB_MsgHdrSize 
**/
uint16 CFE_SB_GetUserDataLength(CFE_SB_MsgPtr_t MsgPtr);

/*****************************************************************************/
/** 
** \brief Sets the length of user data in a software bus message.
**
** \par Description
**          This routine sets the field in the SB message header that determines 
**          the size of the user data in a software bus message.  SB message header 
**          formats can be different for each deployment of the cFE.  So, applications 
**          should use this function rather than trying to poke a length value directly 
**          into their SB message buffers. 
**
** \par Assumptions, External Events, and Notes:
**          - You must set a valid message ID in the SB message header before 
**            calling this function.  
**
** \param[in]  MsgPtr      A pointer to the buffer that contains the software bus message.
**                         This must point to the first byte of the message header.
**
** \param[in]  DataLength  The length to set (size of the user data, in bytes).
**
**
** \sa #CFE_SB_SetMsgId, #CFE_SB_GetUserDataLength, #CFE_SB_SetTotalMsgLength,
**     #CFE_SB_SetMsgTime, #CFE_SB_TimeStampMsg, #CFE_SB_SetCmdCode, #CFE_SB_InitMsg 
**/
void CFE_SB_SetUserDataLength(CFE_SB_MsgPtr_t MsgPtr,uint16 DataLength);

/*****************************************************************************/
/** 
** \brief Gets the total length of a software bus message.
**
** \par Description
**          This routine returns the total size of the software bus message.   
**
** \par Assumptions, External Events, and Notes:
**          - For the CCSDS implementation of this API, the size is derived from
**            the message header.  
**
** \param[in]  MsgPtr      A pointer to the buffer that contains the software bus message.
**                         This must point to the first byte of the message header.
**
** \returns
** \retstmt The total size (in bytes) of the software bus message, including headers.  \endstmt
** \endreturns
**
** \sa #CFE_SB_GetUserData, #CFE_SB_GetMsgId, #CFE_SB_GetUserDataLength, #CFE_SB_SetTotalMsgLength,
**     #CFE_SB_GetMsgTime, #CFE_SB_GetCmdCode, #CFE_SB_GetChecksum, #CFE_SB_MsgHdrSize 
**/
uint16 CFE_SB_GetTotalMsgLength(CFE_SB_MsgPtr_t MsgPtr);

/*****************************************************************************/
/** 
** \brief Sets the total length of a software bus message.
**
** \par Description
**          This routine sets the field in the SB message header that determines 
**          the total length of the message.  SB message header formats can be 
**          different for each deployment of the cFE.  So, applications should 
**          use this function rather than trying to poke a length value directly 
**          into their SB message buffers.    
**
** \par Assumptions, External Events, and Notes:
**          None
**
** \param[in]  MsgPtr      A pointer to the buffer that contains the software bus message.
**                         This must point to the first byte of the message header.
**
** \param[in]  TotalLength The length to set (total size of the message, in bytes, 
**                         including headers).
**
** \sa #CFE_SB_SetMsgId, #CFE_SB_SetUserDataLength, #CFE_SB_GetTotalMsgLength,
**     #CFE_SB_SetMsgTime, #CFE_SB_TimeStampMsg, #CFE_SB_SetCmdCode, #CFE_SB_InitMsg 
**/
void CFE_SB_SetTotalMsgLength(CFE_SB_MsgPtr_t MsgPtr,uint16 TotalLength);

/*****************************************************************************/
/** 
** \brief Gets the checksum field from a software bus message.
**
** \par Description
**          This routine gets the checksum (or other message integrity check 
**          value) from a software bus message.  The contents and location of 
**          this field will depend on the underlying implementation of software 
**          bus messages.  It may be a checksum, a CRC, or some other algorithm.  
**          Users should not call this function as part of a message integrity 
**          check (call #CFE_SB_ValidateChecksum instead).      
**
** \par Assumptions, External Events, and Notes:
**          - If the underlying implementation of software bus messages does not 
**            include a checksum field, then this routine will return a zero.  
**
** \param[in]  MsgPtr      A pointer to the buffer that contains the software bus message.
**                         This must point to the first byte of the message header.
**
** \returns
** \retstmt The checksum included in the software bus message header (if present), otherwise,
**         returns a checksum value of zero.  \endstmt
** \endreturns
**
** \sa #CFE_SB_GetUserData, #CFE_SB_GetMsgId, #CFE_SB_GetUserDataLength, #CFE_SB_GetTotalMsgLength,
**     #CFE_SB_GetMsgTime, #CFE_SB_GetCmdCode, #CFE_SB_GetChecksum, #CFE_SB_MsgHdrSize,
**     #CFE_SB_ValidateChecksum, #CFE_SB_GenerateChecksum 
**/
uint16 CFE_SB_GetChecksum(CFE_SB_MsgPtr_t MsgPtr);

/*****************************************************************************/
/** 
** \brief Calculates and sets the checksum of a software bus message
**
** \par Description
**          This routine calculates the checksum of a software bus message according 
**          to an implementation-defined algorithm.  Then, it sets the checksum field 
**          in the message with the calculated value.  The contents and location of 
**          this field will depend on the underlying implementation of software bus 
**          messages.  It may be a checksum, a CRC, or some other algorithm.        
**
** \par Assumptions, External Events, and Notes:
**          - If the underlying implementation of software bus messages does not 
**            include a checksum field, then this routine will do nothing.  
**
** \param[in]  MsgPtr      A pointer to the buffer that contains the software bus message.
**                         This must point to the first byte of the message header.
**
** \sa #CFE_SB_ValidateChecksum, #CFE_SB_GetChecksum
**/
void CFE_SB_GenerateChecksum(CFE_SB_MsgPtr_t MsgPtr);

/*****************************************************************************/
/** 
** \brief Validates the checksum of a software bus message.
**
** \par Description
**          This routine calculates the expected checksum of a software bus message 
**          according to an implementation-defined algorithm.  Then, it checks the 
**          calculated value against the value in the message's checksum.  If the 
**          checksums do not match, this routine will generate an event message 
**          reporting the error.        
**
** \par Assumptions, External Events, and Notes:
**          - If the underlying implementation of software bus messages does not 
**            include a checksum field, then this routine will always return \c TRUE.  
**
** \param[in]  MsgPtr      A pointer to the buffer that contains the software bus message.
**                         This must point to the first byte of the message header.
**
** \returns
** \retcode TRUE  \retdesc The checksum field in the packet is valid.   \endcode
** \retcode FALSE \retdesc The checksum field in the packet is not valid or the message type is wrong. \endcode
** \endreturns
**
** \sa #CFE_SB_GenerateChecksum, #CFE_SB_GetChecksum
**/
boolean CFE_SB_ValidateChecksum(CFE_SB_MsgPtr_t MsgPtr);


#endif  /* _cfesb_ */
/*****************************************************************************/
