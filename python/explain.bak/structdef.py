#!/usr/bin/python
#-------------------------------------------------------------------------------
# structdef.py
#
# This class contains the structure definition.
#
# Mathew Benson (mbenson@windhoverlabs.com)

from explain.attribdef import *

class StructDef(object):
    def __init__(self, msgid, name):
        """ 
        """
        self.msgid = msgid
        self.name = name
        self.list = []


    def add_attribute(self, name, offset, size, ctype):
        """ 
        """
        attrib = AttributeDef(name, offset, size, ctype)
        self.list.append(attrib)


