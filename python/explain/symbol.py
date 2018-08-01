import struct
from collections import Mapping

from explain.map import SymbolMap, FieldMap
from explain.explain_error import ExplainError


# These are the types that struct knows how to unpack.
# Custom types are below.
STRUCT_MAPPING = {
    'char': 'b',
    'unsigned char': 'B',
    'short': 'h',
    'unsigned short': 'H',
    'int': 'i',
    'unsigned int': 'I',
    'long': 'l',
    'unsigned long': 'L',
    'long long': 'q',
    'unsigned long long': 'Q',
    'float': 'f',
    'double': 'd',
    'ptr': 'P'
}
# Custom types that map different type names to common types.
STRUCT_MAPPING['long unsigned int'] = STRUCT_MAPPING['unsigned long']
STRUCT_MAPPING['short unsigned int'] = STRUCT_MAPPING['unsigned short']
STRUCT_MAPPING['long long unsigned int'] = STRUCT_MAPPING['unsigned long long']


def struct_fmt(symbol: SymbolMap):
    # print("fmt: ", symbol.name)
    try:
        fmt = STRUCT_MAPPING[symbol.name]
    except KeyError as e:
        if '*' in symbol.name:
            bit64 = symbol.byte_size == 8
            mapping = 'unsigned long' if bit64 else 'unsigned int'
            fmt = STRUCT_MAPPING[mapping]
        elif symbol.byte_size == 4:
            fmt = STRUCT_MAPPING['unsigned int']
        else:
            raise ExplainError('Can\'t unpack type {!r}'
                               .format(symbol.name)) from e
    return fmt


def unpack(symbol, buffer, offset, little_endian=None):
    """Use the struct module to unpack a single part of a structure.

    This is slightly inefficient because each member of the struct has to be
    unpacked individually, but it's easier this way due to how Symbols are
    dynamically defined. There isn't a preset list of Symbols.
    """
    end = '<' if (little_endian if little_endian is not None
                  else symbol.elf.little_endian) else '>'
    b = struct.unpack_from(end + struct_fmt(symbol), buffer, offset)[0]
    return b


class Symbol(Mapping):
    def __init__(self, symbol_map: SymbolMap, symbol_buffer: memoryview,
                 offset: int=0, little_endian=None):
        self.buffer = symbol_buffer
        self.little_endian = little_endian if little_endian is not None \
            else symbol_map.elf.little_endian
        self.offset = offset
        self.symbol = symbol_map

    def __getitem__(self, key):
        field = self.symbol.field(key)
        bit_field = field.bit_field
        byte_offset = field.byte_offset
        kind = field.type.simple
        array = kind.array
        # TODO Unify if possible
        if bit_field:
            return BitField(field, self.buffer, self.offset + byte_offset)
        elif array:
            return ArraySymbol(array.type.simple, self.buffer, self.offset +
                               byte_offset, array.multiplicity,
                               self.little_endian)
        else:
            return Symbol(kind, self.buffer, self.offset + byte_offset,
                          self.little_endian)

    def __iter__(self):
        if self.symbol.pointer:
            return
        for field in self.symbol.fields():
            yield field.name

    def __len__(self):
        return len(list(self.symbol.fields()))

    def __repr__(self):
        return 'Symbol({}, offset={})'.format(self.symbol.name, self.offset)

    @property
    def value(self):
        try:
            return unpack(self.symbol, self.buffer, self.offset,
                          self.little_endian)
        except ExplainError:
            ofst = self.offset
            byte_size = self.symbol.byte_size
            return '{} bytes: {}'.format(byte_size, self)


class ArraySymbol(Symbol, list):
    def __init__(self, symbol_map: SymbolMap, buffer: memoryview, offset: int,
                 count: int, little_endian=None):
        super().__init__(symbol_map, buffer, offset, little_endian)
        unit_byte_size = self.symbol.byte_size
        self.extend(
            Symbol(self.symbol, self.buffer, self.offset + (unit_byte_size * i))
            for i in range(count))

    def __getitem__(self, item):
        return list.__getitem__(self, item)

    def __iter__(self):
        return list.__iter__(self)

    def __repr__(self):
        list_str = super(ArraySymbol, self).__repr__()
        return 'ArrayField(values={}, offset={})'.format(list_str, self.offset)


class Field(object):
    def __init__(self, field_map: FieldMap, buffer: memoryview, offset: int):
        self.field = field_map
        self.buffer = buffer
        self.offset = offset


class BitField(Field):
    def __init__(self, field_map: FieldMap, buffer: memoryview,
                 byte_offset: int):
        super().__init__(field_map, buffer, byte_offset)
        self.bit_field = field_map.bit_field
        if self.bit_field is None:
            raise ExplainError('This is not a bit field.')

    def __repr__(self):
        return 'BitField(value={!r}, byte_offset={}, bit_offset={})'.format(
            self.value, self.offset, self.bit_field.bit_offset)

    @property
    def value(self):
        bit_size = self.bit_field.bit_size
        bit_offset = self.bit_field.bit_offset
        if bit_offset < 0:
            raise ExplainError('Can\'t handle negative bit offset now.')
        field_type = self.field.type
        symbol_byte_size = field_type.byte_size
        symbol_bit_size = symbol_byte_size * 8
        shift = (symbol_bit_size - bit_offset - bit_size)
        mask = pow(2, bit_size) - 1
        buffer = self.buffer[self.offset:self.offset+symbol_byte_size]
        buffer = reversed(buffer) if field_type.elf.little_endian else buffer
        memory = 0
        for b in buffer:
            memory = (memory << 8) + b
        bits = (memory >> shift) & mask
        if self.bit_field.bit_size == 1:
            return bits == 1
        return bits
