"""
 
    Copyright (c) 2018 Windhover Labs, L.L.C. All rights reserved.
 
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:
 
  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.
  3. Neither the name Windhover Labs nor the names of its contributors 
     may be used to endorse or promote products derived from this software
     without specific prior written permission.
 
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
  AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
  POSSIBILITY OF SUCH DAMAGE.

"""

from collections import OrderedDict

from explain.map import FieldMap, SymbolMap


def explain_field(f: FieldMap):
    """Return a dictionary representing the given Field with the properties
    needed for this JSON output.

    This method recurses if the field is a non-simple non-pointer kind.
    """
    fd = OrderedDict()
    fd['name'] = f['name']
    # fd['type'] = f.type['name']
    bit_field = f.bit_field
    fd['bit_offset'] = f['byte_offset'] * 8
    kind = f.type
    if f.is_pointer:
        fd['name'] = f.symbol['name']
        fd['bit_size'] = f.symbol['byte_size'] * 8
        fd['base_type'] = '*'
        return fd
    elif not bit_field:
        fd['bit_size'] = f.type['byte_size'] * 8
    else:
        fd['bit_offset'] += bit_field['bit_offset']
        fd['bit_size'] = bit_field['bit_size']
    count, array_type = kind.array
    simple = kind.simple
    if array_type:
        fd['array'] = True
        fd['count'] = count
        fd['type'] = explain_symbol(array_type.simple)
        realtype = f.type['name'].split('_')
        del realtype[0]
        del realtype[-1]
        realtype = '_'.join(realtype)
        fd['real_type'] = realtype
        if "fields" in fd['type']:
            fd['fields'] = fd['type']["fields"]
            del fd['type']["fields"]
    elif not simple.is_base_type:
        fd['fields'] = [explain_field(f) for f in simple.fields]
        fd['real_type'] = f.type['name']
    else:
        fd['base_type'] = simple['name']
        fd['real_type'] = f.type['name']
    return fd


def explain_symbol(symbol: SymbolMap):
    """Return a dictionary representing the given Symbol with the properties
    needed for this JSON output.

    The important properties for this JSON output are the symbol/field name,
    the bit size, and the bit offset. Typedefs are collapsed and in general
    types are ignored/not useful for the use case of this particular JSON.
    """
    sd = OrderedDict()
    sd['name'] = symbol['name']
    sd['bit_size'] = symbol['byte_size'] * 8
    # print(symbol)
    # print(symbol.simple)
    # print(symbol.pointer, symbol.is_primitive, symbol.is_base_type)
    if not symbol.pointer and not symbol.is_primitive:
        sd['fields'] = None if symbol.is_base_type else \
            [explain_field(f) for f in symbol.fields]
        sd['real_type'] = symbol['name']
    else:
        sd['base_type'] = symbol['name']
    return sd


def explain_elf(elf, symbols):
    """Output a JSON to the file-like stream with the symbols from the ELF.

    Currently there is no name for this kind of JSON because it is the only
    kind of output that Explain has right now. When this changes this output
    will need a real name to differentiate it.
    """
    out = OrderedDict()
    out['file'] = elf['name']
    out['little_endian'] = elf['little_endian'] == 1
    out['symbols'] = [explain_symbol(s) for s in symbols]
    return out
