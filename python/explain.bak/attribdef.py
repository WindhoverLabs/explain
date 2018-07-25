#!/usr/bin/python
#-------------------------------------------------------------------------------
# attribdef.py
#
# This class contains the structure definition.
#
# Mathew Benson (mbenson@windhoverlabs.com)


class AttributeDef(object):
    def __init__(self, name, offset, size, ctype):
        """ 
        """
        self.name = name
        self.offset = offset
        self.size = size
        self.ctype = ctype


