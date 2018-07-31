import argparse
import sqlite3
import struct
from abc import ABCMeta
from collections import Mapping

from explain.elf import Elf, SymbolMap, FieldMap
from explain.elf_reader import ElfReader
from explain.explain_error import ExplainError
from explain.sql import SQLiteBacked


class EndOfStream(StopIteration):
    """Raised when a stream has been exhausted."""
    pass


# These are the types that struct knows how to unpack.
# Custom types are below.
BASE_MAPPING = {
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
BASE_MAPPING['long unsigned int'] = BASE_MAPPING['unsigned long']


def struct_fmt(symbol: SymbolMap):
    # print("fmt: ", symbol.name)
    try:
        fmt = BASE_MAPPING[symbol.name]
    except KeyError as e:
        if '*' in symbol.name:
            bit64 = symbol.byte_size == 8
            mapping = 'unsigned long' if bit64 else 'unsigned int'
            fmt = BASE_MAPPING[mapping]
        elif symbol.byte_size == 4:
            fmt = BASE_MAPPING['unsigned int']
        else:
            raise ExplainError('Can\'t unpack type {!r}'
                               .format(symbol.name)) from e
    return fmt


def unpack(symbol, buffer, offset):
    end = '<' if symbol.elf.little_endian else '>'
    b = struct.unpack_from(end + struct_fmt(symbol), buffer, offset)[0]
    return b


class Symbol(Mapping):
    def __init__(self, symbol_map: SymbolMap, symbol_buffer: memoryview, offset: int=0):
        self.buffer = symbol_buffer
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
                               byte_offset, array.multiplicity)
        else:
            return Symbol(kind, self.buffer, self.offset + byte_offset)

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
            return unpack(self.symbol, self.buffer, self.offset)
        except ExplainError:
            ofst = self.offset
            byte_size = self.symbol.byte_size
            return '{} bytes'.format(
                len([hex(b) for b in self.buffer[ofst:ofst+byte_size]]))


class ArraySymbol(Symbol, list):
    def __init__(self, symbol_map: SymbolMap, buffer: memoryview, offset: int,
                 count: int):
        super().__init__(symbol_map, buffer, offset)
        unit_byte_size = self.symbol.byte_size
        self.extend(
            Symbol(self.symbol, self.buffer, self.offset + (unit_byte_size * i))
            for i in range(count))

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
        shift = (8 - bit_offset - bit_size)
        mask = pow(2, bit_size) - 1 << shift
        bits = (self.buffer[self.offset] & mask) >> shift
        if self.bit_field.bit_size == 1:
            return bits == 1
        return bits


class StreamParser(SQLiteBacked):
    def __init__(self, database, stream):
        super().__init__(database)
        self.stream = stream

    def read(self, num_bytes):
        b = self.stream.read(num_bytes)
        if len(b) != num_bytes:
            raise EndOfStream
        return b

    def _get_symbol_name(self):
        header_size = 4
        b = self.read(header_size)
        name = 'MACHINE'
        # print('{} -> {}'.format(b, name))
        return name

    def parse(self):
        elf = Elf.from_name(self.database, 'CF.so')
        while True:
            name = self._get_symbol_name()
            symbol = elf.symbol(name)
            bts = memoryview(self.read(symbol.byte_size))
            yield Symbol(symbol, bts)


def pretty(symbol, indent=0):
    i = '| ' * indent
    for name, value in symbol.items():
        print('{}{} = {!r}'.format(i, name, value))
        if isinstance(value, Symbol):
            pretty(value, indent=indent+1)


def flatten(symbol, name=''):
    # print(symbol)
    if isinstance(symbol, ArraySymbol):
        if 'char' in symbol.symbol.name:
            print('{} = {!r}'.format(name, ''.join(chr(c.value) for c in symbol)))
        else:
            for n, elem in enumerate(symbol):
                flatten(elem, name + '[{}]'.format(n))
    else:
        print('{} = {}'.format(name, symbol.value))
        if isinstance(symbol, Symbol):
            for n, elem in symbol.items():
                flatten(elem, name + '.' + n)


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--database', default=':memory:',
                        help='database to read from')
    source.add_argument('--elf', help='ELF file to dynamically load')
    parser.add_argument('stream', help='stream to parse')

    args = parser.parse_args()
    stream = open(args.stream, 'rb')

    database = sqlite3.connect(args.database)
    if args.elf is not None:
        reader = ElfReader(database)
        reader.insert_elf(args.elf)

    stream_parser = StreamParser(database, stream)
    parsed = stream_parser.parse()
    for p in parsed:
        # print(p.symbol.name)
        # pretty(p, indent=1)
        # print(p['nak']['gap'])
        flatten(p, 'MACHINE')


if __name__ == '__main__':
    main()
