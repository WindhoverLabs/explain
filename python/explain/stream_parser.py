import argparse
import sqlite3
from abc import abstractmethod
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


class StreamParser(SQLiteBacked):
    def __init__(self, database, stream):
        super().__init__(database)
        self.stream = stream

    def read(self, num_bytes):
        b = self.stream.read(num_bytes)
        if len(b) != num_bytes:
            raise EndOfStream
        return b

    @abstractmethod
    def advance_stream_to_structure(self) -> str:
        """Advance the stream to the next structure and return the name of the
        structure."""
        raise NotImplementedError

    def parse(self):
        while True:
            name = self.advance_stream_to_structure()
            symbol = SymbolMap.from_name(self.database, name)
            bts = memoryview(self.read(symbol.byte_size))
            yield Symbol(symbol, bts)


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
        flatten(p, 'MACHINE')


if __name__ == '__main__':
    print(
        'This is an abstract script. Users should subclass StreamParser in\n'
        'their own code and may then optionally call the main method of this\n'
        'script to invoke some basic command line parsing.')
    exit(0)
