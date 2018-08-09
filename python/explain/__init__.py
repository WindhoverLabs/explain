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
    elif not simple.is_base_type:
        fd['fields'] = [explain_field(f) for f in simple.fields]
    else:
        fd['base_type'] = simple['name']
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