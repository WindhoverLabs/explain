import struct
from collections import Mapping

from explain.explain_error import ExplainError
from explain.map import SymbolMap, BitFieldMap


def unpack(fmt, buffer, offset, little_endian):
    """Use the struct module to unpack a single part of a structure.

    This is slightly inefficient because each member of the struct has to be
    unpacked individually, but it's easier this way due to how Symbols are
    dynamically defined. There isn't a preset list of Symbols.
    """
    b = struct.unpack_from(('<' if little_endian else '>') + fmt, buffer, offset)[0]
    return b


class Symbol(Mapping):
    """A representation of a Symbol in a buffer of memory."""

    __slots__ = ('buffer', 'little_endian', 'offset', 'symbol_map', 'value')

    def __init__(self, symbol_map: SymbolMap, buffer: memoryview,
                 offset: int, little_endian=None):
        self.buffer = buffer
        self.little_endian = little_endian if little_endian is not None \
            else symbol_map.little_endian
        self.offset = offset
        self.symbol_map = symbol_map
        if symbol_map.is_primitive:
            self.value = unpack(symbol_map.fmt, buffer, offset, little_endian)

    def __getitem__(self, key):
        field = self.symbol_map.field(key)
        bit_field = field.bit_field
        kind = field.type.simple
        symbol_offset = self.offset + field['byte_offset']
        array = kind.array
        if bit_field:
            symbol = BitFieldSymbol(
                symbol_map=kind,
                bit_field=bit_field,
                buffer=self.buffer,
                offset=symbol_offset,
                little_endian=self.little_endian
            )
        elif array:
            symbol = ArraySymbol(
                symbol_map=kind,
                buffer=self.buffer,
                offset=symbol_offset,
                count=array['multiplicity'],
                unit_symbol=array.type,
                little_endian=self.little_endian
            )
        else:
            symbol = Symbol(
                symbol_map=kind,
                buffer=self.buffer,
                offset=symbol_offset,
                little_endian=self.little_endian
            )
        return symbol

    def __iter__(self):
        if self.symbol_map.pointer:
            return
        for field in self.symbol_map.fields:
            yield field['name']

    def __len__(self):
        return len(self.symbol_map.fields)

    def __repr__(self):
        return 'Symbol({}, offset={})'.format(self.symbol_map['name'], self.offset)

    def flatten(self, name=''):
        name = name or self.symbol_map['name']
        # print('flatten {} {} {} {}'.format(name, self.symbol_map, self.offset, self.symbol_map.is_base_type))
        if self.symbol_map.is_primitive:
            yield name, self.value
        else:
            name_dot = name + '.'
            for field_name, symbol in self.items():
                yield from symbol.flatten(name_dot + field_name)


class ArraySymbol(Symbol):
    """A representation of an array from a buffer of memory."""

    def __init__(self, symbol_map: SymbolMap, buffer: memoryview,
                 offset: int, count: int, unit_symbol: SymbolMap,
                 little_endian=None):
        super().__init__(symbol_map=symbol_map, buffer=buffer, offset=offset,
                         little_endian=little_endian)
        unit_byte_size = unit_symbol['byte_size']
        self.array = [0]*count
        for i in range(count):
            self.array[i] = Symbol(unit_symbol, self.buffer, self.offset + (unit_byte_size * i))

    def __getitem__(self, item):
        return list.__getitem__(self.array, item)

    def __iter__(self):
        return list.__iter__(self.array)

    def __repr__(self):
        list_str = super(ArraySymbol, self).__repr__()
        return 'ArrayField(values={}, offset={})'.format(list_str, self.offset)

    def flatten(self, name=''):
        for n, elem in enumerate(self):
            yield from elem.flatten('{}[{}]'.format(name, n))


class BitFieldSymbol(Symbol):
    """A representation of a bitfield from a buffer of memory."""
    def __init__(self, symbol_map: SymbolMap, bit_field: BitFieldMap,
                 buffer: memoryview, offset: int, little_endian=None):
        super().__init__(symbol_map, buffer, offset, little_endian)
        self.bit_field = bit_field
        if self.bit_field is None:
            raise ExplainError('bit_field is not allowed to be None.')
        self.value = self._value()

    def __iter__(self):
        raise ExplainError('Please don\'t iterate over a bitfield.')

    def __repr__(self):
        return 'BitField(value={!r}, byte_offset={}, bit_offset={})'.format(
            self.value, self.offset, self.bit_field['bit_offset'])

    def flatten(self, name=''):
        yield name, self.value

    def _value(self):
        bit_size = self.bit_field['bit_size']
        bit_offset = self.bit_field['bit_offset']
        if bit_offset < 0:
            # Negative bit offsets might "just work", but I don't know.
            # Test when encountered.
            raise ExplainError('Can\'t handle negative bit offset now.')
        field_type = self.symbol_map
        symbol_byte_size = field_type['byte_size']
        symbol_bit_size = symbol_byte_size * 8
        shift = (symbol_bit_size - bit_offset - bit_size)
        mask = pow(2, bit_size) - 1
        buffer = self.buffer[self.offset:self.offset + symbol_byte_size]
        buffer = reversed(buffer) if self.little_endian else buffer
        memory = 0
        for b in buffer:
            memory = (memory << 8) + b
        bits = (memory >> shift) & mask
        if self.bit_field['bit_size'] == 1:
            return bits == 1
        return bits
