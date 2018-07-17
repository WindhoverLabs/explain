#!/usr/bin/python
#-------------------------------------------------------------------------------
# pyexplain.py
#
# This utility parses an elf image and generates memory bitmaps for the 
# libexplain library.
#
# Mathew Benson (mbenson@windhoverlabs.com)
#-------------------------------------------------------------------------------
from __future__ import print_function

import elftools.dwarf.compileunit
from structdef import *
import json
import argparse

class MyCompileUnit(elftools.dwarf.compileunit.CompileUnit):

    def get_DIE_at_offset(self, offset):
        for die in self.iter_DIEs():
            if die.offset == offset:
                return die 
        return None

elftools.dwarf.compileunit.CompileUnit = MyCompileUnit

import sys

# If pyelftools is not installed, the utility can also run from the root dir of 
# the source distribution.
sys.path[0:0] = ['.', '..']

from elftools.elf.elffile import ELFFile

def process_file(filename, symbol):
    print('Processing file:', filename)
    with open(filename, 'rb') as f:
        elffile = ELFFile(f)

        if elffile.little_endian == True :
            endian = 'L'
        else :
            endian = 'B'

        if not elffile.has_dwarf_info():
            print('  file has no DWARF info')
            return

        # get_dwarf_info returns a DWARFInfo context object, which is the
        # starting point for all DWARF-based processing in pyelftools.
        dwarfinfo = elffile.get_dwarf_info()

        for CU in dwarfinfo.iter_CUs():
            # DWARFInfo allows to iterate over the compile units contained in
            # the .debug_info section. CU is a CompileUnit object, with some
            # computed attributes (such as its offset in the section) and
            # a header which conforms to the DWARF standard. The access to
            # header elements is, as usual, via item-lookup.
            #print('  Found a compile unit at offset %s, length %s' % (
            #    CU.cu_offset, CU['unit_length']))

            # Start with the top DIE, the root for this CU's DIE tree
            top_DIE = CU.get_top_DIE()
            #print('    Top DIE with tag=%s' % top_DIE.tag)

            # We're interested in the filename...
            #print('    name=%s' % top_DIE.get_full_path())

            # Display DIEs recursively starting with top_DIE
            return endian, die_info_rec(top_DIE, CU, symbol)

def die_info_rec(die, CU, symbol, struct = None):
    """ A recursive function for showing information about a DIE and its
        children.
    """
    if die.get_full_path() == symbol :
        try:
            struct_die = CU.get_DIE_at_offset(die.attributes['DW_AT_type'].value)
        except KeyError, e:
            print ('KeyError, ensure that the structure does not have a tag, key: %s' % (str(e)))
            print ('Exiting...')
            sys.exit(1)
        if struct_die is not None :
            struct = StructDef(-1, die.get_full_path())
            die_structure_type_rec(struct_die, CU, struct)
  
    for child in die.iter_children():
        struct = die_info_rec(child, CU, symbol, struct)
    
    return struct


def die_structure_type_rec(die, CU, struct):
    """ A recursive function for showing information about a DIE and its
        children.
    """  
    for child in die.iter_children():
        die_member_rec(child, CU, struct)


def die_member_rec(die, CU, struct):
    """ A recursive function for showing information about a DIE and its
        children.
    """
    byte_offset_attrib = die.attributes.get('DW_AT_data_member_location', None)
    byte_size_attrib = die.attributes.get('DW_AT_byte_size', None)
    bit_size_attrib = die.attributes.get('DW_AT_bit_size', None)
    bit_offset_attrib = die.attributes.get('DW_AT_bit_offset', None)
    
    byte_offset = 0
    byte_size = 0
    bit_length = 0
    bit_offset = 0

    if byte_offset_attrib is not None :
        byte_offset = byte_offset_attrib.value

    if byte_size_attrib is not None :
        byte_size = byte_size_attrib.value

    if bit_size_attrib is not None :
        bit_length = bit_size_attrib.value

    if bit_offset_attrib is not None :
        bit_offset = bit_offset_attrib.value

    bit_offset = bit_offset + (byte_offset * 8)

    if bit_length == 0 :
        bit_length = get_bit_length_from_at_type(CU.get_DIE_at_offset(die.attributes['DW_AT_type'].value), CU)
        
    field_name = die.get_full_path()
    struct.add_attribute(field_name, bit_offset, bit_length, 'UNKNOWN')


def get_bit_length_from_at_type(die, CU):
    bit_length = -1

    if die.tag == 'DW_TAG_array_type' :
        upper_bound = -1
        for child in die.iter_children():
            upper_bound_temp = parse_array_type_child(child, CU)
            if upper_bound_temp != -1 :
                upper_bound = upper_bound_temp

        bit_length = get_bit_length_from_at_type(CU.get_DIE_at_offset(die.attributes['DW_AT_type'].value), CU) * upper_bound
    else :
        byte_size_attrib = die.attributes.get('DW_AT_byte_size', None)
        
    
        if byte_size_attrib is None :
            bit_length = get_bit_length_from_at_type(CU.get_DIE_at_offset(die.attributes['DW_AT_type'].value), CU)
        else :
            byte_size = byte_size_attrib.value
            bit_length = byte_size * 8  

    return bit_length


def parse_array_type_child(die, CU) :
    upper_bound = -1
    upper_bound_attrib = die.attributes.get('DW_AT_upper_bound', None)

    if upper_bound_attrib is not None :
        # Array size is calculated as (DW_AT_upper_bound - DW_AT_lower_bound) + 1.
        upper_bound = upper_bound_attrib.value + 1
    return upper_bound


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate bitmap files directly from as-built ELF files for the libextract library.')
    parser.add_argument('-o', '--output', metavar='<file name>', type=str, help='Output file name', required=True)
    parser.add_argument('-m', '--msgid', metavar='<number>', type=str, help='Message ID.  0x0000 to 0x1fff', required=True)
    parser.add_argument('-ss', '--src-symbol', metavar='<structure name>', type=str, help='Source symbol name.', required=True)
    parser.add_argument('-ds', '--dst-symbol', metavar='<structure name>', type=str, help='Destination symbol name', required=True)
    parser.add_argument('-sf', '--src-file', metavar='<file name>', type=str, help='Source file', required=True)
    parser.add_argument('-df', '--dst-file', metavar='<file name>', type=str, help='Destination file', required=True)
    parser.add_argument('-a', '--append', action='store_true', help='Append to output file.', required=False)

    args = parser.parse_args()

    source_endian, source_struct = process_file(args.src_file, args.src_symbol)
    dest_endian, dest_struct = process_file(args.dst_file, args.dst_symbol)


    # Check that process_file returned a value
    if source_struct == None or dest_struct == None:
        print ('Error, source or destination structure not found')
        print ('Ensure the structure is used, that the compiler has not optimized it out, and that a tag is not used.')
        print ('Exiting...')
        sys.exit(1)

    if args.append == False :
        output = {'bitmap': []}
    else :
        with open(args.output, 'r') as json_data:
            output = json.load(json_data)
            json_data.close()

    struct = {
        'id':args.msgid,
        'src_symbol':args.src_symbol,
        'dst_symbol':args.dst_symbol,
        'ops_name':'',
        'src_endian':source_endian,
        'dst_endian':dest_endian,
        'fields':[]
    }

    fields = struct['fields']

    for i in range(0, len(source_struct.list)) :
        field = {
            'op_name': source_struct.list[i].name, 
            'length': source_struct.list[i].size, 
            'src_offset': source_struct.list[i].offset,
            'dst_offset': dest_struct.list[i].offset}
        fields.append(field)

    output['bitmap'].append(struct)
    
    print('Writing file %s:' % (args.output))
    with open(args.output, 'w') as outfile :
        json.dump(output, outfile, sort_keys=False, indent=4, separators=(',', ': '))

