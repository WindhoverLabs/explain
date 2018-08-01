import argparse
import sqlite3
from abc import abstractmethod, ABCMeta
from io import RawIOBase
from typing import Type

from explain.explain_error import ExplainError
from explain.map import SymbolMap
from explain.elf_reader import ElfReader
from explain.sql import SQLiteBacked
from explain.symbol import Symbol
from explain.util import flatten


class EndOfStream(ExplainError, StopIteration):
    """Raised when a stream has been exhausted."""
    pass


class StreamCache(RawIOBase):
    def __init__(self, stream):
        self.stream = stream
        self.cache = bytes()

    def clear(self):
        self.cache = bytes()

    def read(self, size: int = ...):
        to_read = max(0, size - len(self.cache))
        read = self.stream.read(to_read)
        if len(read) != to_read:
            raise EndOfStream
        self.cache += read
        return self.cache


class StreamParser(SQLiteBacked, metaclass=ABCMeta):
    def __init__(self, database, stream):
        super().__init__(database)
        self.stream = StreamCache(stream)

    @abstractmethod
    def advance_stream_to_structure(self) -> str:
        """Advance the stream to the next structure and return the name of the
        structure."""
        raise NotImplementedError

    def parse(self):
        while True:
            name = self.advance_stream_to_structure()
            yield self.read_symbol(SymbolMap.from_name(self.database, name))
            self.stream.clear()

    def read_symbol(self, symbol_map: SymbolMap, little_endian=None):
        bts = memoryview(self.stream.read(symbol_map.byte_size))
        return Symbol(symbol_map, bts, little_endian=little_endian)


class CcsdsMixin(StreamParser):
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.ccsds_map = SymbolMap.from_name(self.database, 'CCSDS_PriHdr_t')

    def advance_stream_to_structure(self):
        ccsds = self.read_symbol(self.ccsds_map)
        # flatten(ccsds, 'ccsds', join_chr=False)
        stream_id, length = ccsds['StreamId'], ccsds['Length']
        app_id = (stream_id[0].value << 8) + stream_id[1].value
        length = (length[0].value << 8) + length[1].value + 7
        self.stream.read(length)
        if app_id == 0xA13:
            return 'PX4_DistanceSensorMsg_t'
        else:
            print('App ID not 0xA13: ', hex(app_id))
            raise EndOfStream


class CfeStreamParser(StreamParser):
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.cfe_header = self.read_symbol(
            SymbolMap.from_name(self.database, 'CFE_FS_Header_t'),
            little_endian=False)
        flatten(self.cfe_header)
        self.stream.clear()


def main(parse_class: Type[StreamParser]):
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

    stream_parser = parse_class(database, stream)
    parsed = stream_parser.parse()
    for p in parsed:
        # print(p.symbol.name)
        # pretty(p, indent=1)
        # print(p['nak']['gap'])
        flatten(p)


if __name__ == '__main__':
    print(
        'This is an abstract script. Users should subclass StreamParser in\n'
        'their own code and may then optionally call the main method of this\n'
        'script to invoke some basic command line parsing.')
    exit(0)
