/******************************************************************************
** File: cfe_sb_util.c
**
**      Copyright (c) 2004-2012, United States government as represented by the
**      administrator of the National Aeronautics Space Administration.
**      All rights reserved. This software(cFE) was created at NASA's Goddard
**      Space Flight Center pursuant to government contracts.
**
**      This is governed by the NASA Open Source Agreement and may be used,
**      distributed and modified only pursuant to the terms of that agreement.
**
**
**
** Purpose:
**      This file contains 'access' macros and functions for reading and
**      writing message header fields.
**
** Author:   R.McGraw/SSI
**
** $Log: cfe_sb_util.c  $
** Revision 1.8 2014/07/10 09:24:08GMT-05:00 rmcgraw 
** DCR9772:1 Changes from C. Monaco & W.M Reid from APL for endianess neutrality
** Revision 1.7 2014/06/06 15:18:37EDT rmcgraw
** DCR21559 - Changed CFE_SB_MsgHdrSize to use macro instead of writing msgid directly
** Revision 1.6 2012/09/27 17:16:04EDT aschoeni
** Fixed 32_32_M_20 get function to shift by 12 instead of masking
** Revision 1.5 2012/01/13 12:15:13EST acudmore
** Changed license text to reflect open source
** Revision 1.4 2011/02/03 15:25:37EST lwalling
** Modified Get/Set time functions to support CFE_SB_PACKET_TIME_FORMAT selection
** Revision 1.3 2010/10/25 13:54:10EDT aschoeni
** Removed unused value from SetUserDataLength
** Revision 1.2 2010/10/04 15:21:13EDT jmdagost
** Cleaned up copyright symbol.
** Revision 1.1 2008/04/17 08:05:32EDT ruperera
** Initial revision
** Member added to project c:/MKSDATA/MKS-REPOSITORY/MKS-CFE-PROJECT/fsw/cfe-core/src/sb/project.pj
** Revision 1.10 2006/10/16 14:31:00EDT rjmcgraw
** Minor changes to comply with MISRA standard
** Revision 1.9 2006/06/12 19:26:06GMT rjmcgraw
** Added legal statement
** Revision 1.8 2006/06/05 15:43:50EDT rjmcgraw
** Comment changes in reference to DCR398
** Revision 1.7 2006/04/28 18:35:14GMT rjmcgraw
** Corrected problems with checksum utils when no sec hdr present
** Revision 1.6 2006/04/28 18:02:20GMT rjmcgraw
** Corrected problems with Set/GetCmdCode for cmd pkts wo sec hdr
** Revision 1.5 2006/04/27 18:45:10GMT rjmcgraw
** Corrected problems with Set/GetMsgTime when no sec hdr is present in tlm pkts
**
******************************************************************************/


/*
** Include Files
*/

#include "cfe_sb.h"
#include "ccsds.h"

#define MESSAGE_FORMAT_IS_CCSDS


/******************************************************************************
**  Function:  CFE_SB_InitMsg()
**
**  Purpose:
**    Initialize the header fields of a message
**
**  Arguments:
**    MsgPtr  - Pointer to the header of a message.
**    MsgId   - MsgId to use for the message.
**    Length  - Length of the message in bytes.
**    Clear   - Indicates whether to clear the entire message:
**                TRUE = fill sequence count and packet data with zeros
**                FALSE = leave sequence count and packet data unchanged
**  Return:
**    (none)
*/
void CFE_SB_InitMsg(void           *MsgPtr,
                    CFE_SB_MsgId_t MsgId,
                    uint16         Length,
                    boolean        Clear )
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    CCSDS_InitPkt ((CCSDS_PriHdr_t *)MsgPtr,(uint16)MsgId,Length,Clear);

#endif
} /* end CFE_SB_InitMsg */



/******************************************************************************
**  Function:  CFE_SB_MsgHdrSize()
**
**  Purpose:
**    Get the size of a message header.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**     Size of Message Header.
*/
uint16 CFE_SB_MsgHdrSize(CFE_SB_MsgId_t MsgId)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    uint16 size;
    CCSDS_PriHdr_t  CCSDSPriHdr;

    CCSDS_WR_SID(CCSDSPriHdr,MsgId);

    /* if secondary hdr is not present... */
    if(CCSDS_RD_SHDR(CCSDSPriHdr) == 0){

        size = sizeof(CCSDS_PriHdr_t);

    }else if(CCSDS_RD_TYPE(CCSDSPriHdr) == CCSDS_CMD){

        size = CFE_SB_CMD_HDR_SIZE;

    }else{

        size = CFE_SB_TLM_HDR_SIZE;
    }

    return size;

#endif
}/* end CFE_SB_MsgHdrSize */


/******************************************************************************
**  Function:  CFE_SB_GetUserData()
**
**  Purpose:
**    Get a pointer to the user data portion of a message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**    Pointer to the first byte after the headers
*/
void *CFE_SB_GetUserData(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS
    uint8           *BytePtr;
    CFE_SB_MsgId_t  MsgId;
    uint16          HdrSize;

    BytePtr = (uint8 *)MsgPtr;
    MsgId = CCSDS_RD_SID(MsgPtr->Hdr);
    HdrSize = CFE_SB_MsgHdrSize(MsgId);

    return (BytePtr + HdrSize);
#endif
}/* end CFE_SB_GetUserData */


/******************************************************************************
**  Function:  CFE_SB_GetMsgId()
**
**  Purpose:
**    Get the message ID of a message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**    The Message Id in the message.
*/
CFE_SB_MsgId_t CFE_SB_GetMsgId(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    return CCSDS_RD_SID(MsgPtr->Hdr);

#endif
}/* end CFE_SB_GetMsgId */


/******************************************************************************
**  Function:  CFE_SB_SetMsgId()
**
**  Purpose:
**    Set the message Id of a message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**    MsgId  - Message Id to be written
**
**  Return:
**    (none)
*/
void CFE_SB_SetMsgId(CFE_SB_MsgPtr_t MsgPtr,
                     CFE_SB_MsgId_t MsgId)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    CCSDS_WR_SID(MsgPtr->Hdr,MsgId);

#endif
}/* end CFE_SB_SetMsgId */


/******************************************************************************
**  Function:  CFE_SB_GetUserDataLength()
**
**  Purpose:
**    Get the length of the user data of a message (total size - hdrs).
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**    Size of the message minus the headers
*/
uint16 CFE_SB_GetUserDataLength(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS
    uint16 TotalMsgSize;
    uint16 HdrSize;

    CFE_SB_MsgId_t MsgId;
    MsgId = CCSDS_RD_SID(MsgPtr->Hdr);
    TotalMsgSize = CFE_SB_GetTotalMsgLength(MsgPtr);
    HdrSize = CFE_SB_MsgHdrSize(MsgId);

    return (TotalMsgSize - HdrSize);
#endif
}/* end CFE_SB_GetUserDataLength */


/******************************************************************************
**  Function:  CFE_SB_SetUserDataLength()
**
**  Purpose:
**    Set the length field in the hdr, given the user data length.
**
**  Arguments:
**    MsgPtr     - Pointer to a CFE_SB_Msg_t
**    DataLength - Length of the user data
**
**  Return:
**    (none)
*/
void CFE_SB_SetUserDataLength(CFE_SB_MsgPtr_t MsgPtr,uint16 DataLength)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    uint32 TotalMsgSize, HdrSize;

    CFE_SB_MsgId_t MsgId;
    MsgId = CCSDS_RD_SID(MsgPtr->Hdr);
    HdrSize = CFE_SB_MsgHdrSize(MsgId);
    TotalMsgSize = HdrSize + DataLength;
    CCSDS_WR_LEN(MsgPtr->Hdr,TotalMsgSize);

#endif
}/* end CFE_SB_SetUserDataLength */


/******************************************************************************
**  Function:  CFE_SB_GetTotalMsgLength()
**
**  Purpose:
**    Get the total length of the message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**    Total Length of the message
*/
uint16 CFE_SB_GetTotalMsgLength(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    return CCSDS_RD_LEN(MsgPtr->Hdr);

#endif
}/* end CFE_SB_GetTotalMsgLength */


/******************************************************************************
**  Function:  CFE_SB_SetTotalMsgLength()
**
**  Purpose:
**    Set the length field, given the total length of the message.
**
**  Arguments:
**    MsgPtr      - Pointer to a CFE_SB_Msg_t
**    TotalLength - Total Length of the message
**
**  Return:
**    (none)
*/
void CFE_SB_SetTotalMsgLength(CFE_SB_MsgPtr_t MsgPtr,uint16 TotalLength)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    CCSDS_WR_LEN(MsgPtr->Hdr,TotalLength);

#endif
}/* end CFE_SB_SetTotalMsgLength */


/******************************************************************************
**  Function:  CFE_SB_GetChecksum()
**
**  Purpose:
**    Get the checksum field of message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**
*/
uint16 CFE_SB_GetChecksum(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    CFE_SB_CmdHdr_t     *CmdHdrPtr;

    /* if msg type is telemetry or there is no secondary hdr... */
    if((CCSDS_RD_TYPE(MsgPtr->Hdr) == CCSDS_TLM)||(CCSDS_RD_SHDR(MsgPtr->Hdr) == 0)){
        return 0;
    }/* end if */

    /* cast the input pointer to a Cmd Msg pointer */
    CmdHdrPtr = (CFE_SB_CmdHdr_t *)MsgPtr;

    return CCSDS_RD_CHECKSUM(CmdHdrPtr->Sec);

#endif
}/* end CFE_SB_GetChecksum */


/******************************************************************************
**  Function:  CFE_SB_GenerateChecksum()
**
**  Purpose:
**    Calculate and Set the checksum field of message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Note: If any header fields are changed after this call, the checksum will
**        no longer be valid.
**        Also, the packet length field dictates the number of iterations
**        used in the checksum algorithm and therefore must be properly set
**        before calling this function.
**
**  Return:
**    (none)
*/
void CFE_SB_GenerateChecksum(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    CCSDS_CmdPkt_t    *CmdPktPtr;

    /* if msg type is telemetry or there is no secondary hdr... */
    if((CCSDS_RD_TYPE(MsgPtr->Hdr) == CCSDS_TLM)||(CCSDS_RD_SHDR(MsgPtr->Hdr) == 0)){
        return;
    }/* end if */

    CmdPktPtr = (CCSDS_CmdPkt_t *)MsgPtr;

    CCSDS_LoadCheckSum(CmdPktPtr);

#endif
}/* end CFE_SB_GenerateChecksum */


/******************************************************************************
**  Function:  CFE_SB_ValidateChecksum()
**
**  Purpose:
**    Validate the checksum field of message.
**
**  Arguments:
**    MsgPtr - Pointer to a CFE_SB_Msg_t
**
**  Return:
**    TRUE if checksum of packet is valid; FALSE if not.
*/
boolean CFE_SB_ValidateChecksum(CFE_SB_MsgPtr_t MsgPtr)
{
#ifdef MESSAGE_FORMAT_IS_CCSDS

    CCSDS_CmdPkt_t    *CmdPktPtr;

    /* if msg type is telemetry or there is no secondary hdr... */
    if((CCSDS_RD_TYPE(MsgPtr->Hdr) == CCSDS_TLM)||(CCSDS_RD_SHDR(MsgPtr->Hdr) == 0)){
        return FALSE;
    }/* end if */

    CmdPktPtr = (CCSDS_CmdPkt_t *)MsgPtr;

    return CCSDS_ValidCheckSum (CmdPktPtr);

#endif
}/* end CFE_SB_ValidateChecksum */

