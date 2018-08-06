import argparse
import json
import os
import sqlite3
from abc import abstractmethod, ABCMeta
from collections import namedtuple, OrderedDict
from csv import DictWriter
from io import RawIOBase
from time import time
from typing import Type, Dict

from explain.explain_error import ExplainError
from explain.map import SymbolMap
from explain.elf_reader import ElfReader
from explain.sql import SQLiteBacked
from explain.symbol import Symbol


class EndOfStream(ExplainError, StopIteration):
    """Raised when a stream has been exhausted."""
    pass


class StreamCache(RawIOBase):
    """Caches stream output until cleared.

    Reads from the StreamCache are always performed from the start of the
    current cache, thus multiple reads of the same amount will return the same
    data as long as the cache has not been cleared.
    """
    def __init__(self, stream):
        self.stream = stream
        self.cache = bytes()
        self.cache_len = 0

    def clear(self):
        self.cache = bytes()
        self.cache_len = 0

    def read(self, size: int = ...):
        to_read = max(0, size - self.cache_len)
        read = self.stream.read(to_read)
        len_read = len(read)
        if len_read != to_read:
            raise EndOfStream
        self.cache += read
        self.cache_len += len_read
        return self.cache


class StreamParser(SQLiteBacked, metaclass=ABCMeta):
    """"""

    def __init__(self, database, stream):
        super().__init__(database)
        self.stream = StreamCache(stream)

    @abstractmethod
    def get_structure_name(self) -> str:
        """Advance the stream to the next structure and return the name of the
        structure."""
        raise NotImplementedError

    def parse(self):
        while True:
            name = self.get_structure_name()
            yield self.read_symbol(SymbolMap.from_name(self.database, name))
            self.stream.clear()

    def read_symbol(self, symbol_map: SymbolMap, little_endian=None):
        bts = memoryview(self.stream.read(symbol_map['byte_size']))
        return Symbol(symbol_map, bts, 0, little_endian=little_endian)


class CcsdsMixin(StreamParser):
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.ccsds_map = SymbolMap.from_name(self.database, 'CCSDS_PriHdr_t')
        with open(os.path.join(
                os.path.dirname(__file__), 'ccsds_map.json')) as fp:
            self.msg_map = {int(k, 0): v for k, v in json.load(fp).items()}

    def get_structure_name(self):
        ccsds = self.read_symbol(self.ccsds_map)
        stream_id, length = ccsds['StreamId'], ccsds['Length']
        app_id = (stream_id[0].value << 8) + stream_id[1].value
        length = (length[0].value << 8) + length[1].value + 7
        self.stream.read(length)
        try:
            return self.msg_map[app_id]
        except KeyError:
            print('App ID not recognized: ', hex(app_id))
            raise EndOfStream


class CfeStreamParser(StreamParser, metaclass=ABCMeta):
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.cfe_header = self.read_symbol(
            SymbolMap.from_name(self.database, 'CFE_FS_Header_t'),
            little_endian=False)
        self.stream.clear()


class DsStreamParser(CfeStreamParser, CcsdsMixin):
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.ds_header = self.read_symbol(
            SymbolMap.from_name(database, 'DS_FileHeader_t'))
        self.stream.clear()


def main(parse_class: Type[StreamParser]):
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--database', default=':memory:',
                        help='database to read from')
    source.add_argument('--elf', help='ELF file to dynamically load')
    parser.add_argument('stream', help='stream (file) to parse')
    parser.add_argument('--csv', help='directory to put output csv files')

    args = parser.parse_args()
    stream = open(args.stream, 'rb')

    database = sqlite3.connect(args.database)
    if args.elf is not None:
        reader = ElfReader(database)
        reader.insert_elf(args.elf)

    CsvFilePair = namedtuple('CsvFilePair', ['csv', 'file'])
    csvs = {}  # type: Dict[str, CsvFilePair]
    path = os.path.curdir
    if args.csv:
        path = os.path.join(path, args.csv)

    stream_parser = parse_class(database, stream)
    start_time = time()

    def prog(s):
        for n, p in enumerate(s):
            if not n % 1000:
                print('{:6d}, {:.2f}'.format(n, time() - start_time))
                if n >= 30000:
                    raise StopIteration
            yield p

    try:
        for symbol in prog(stream_parser.parse()):
            name = symbol.symbol['name']
            flat = OrderedDict(symbol.flatten())
            if name not in csvs:
                file = open(os.path.join(path, name + '.csv'), 'w')
                fieldnames = flat.keys()
                csv = DictWriter(file, fieldnames=fieldnames)
                csv.writeheader()
                csvs[name] = CsvFilePair(csv, file)
            csv = csvs[name].csv
            csv.writerow(flat)
    finally:
        for _, file in csvs.values():
            file.close()


if __name__ == '__main__':
    main(DsStreamParser)
    # print(
    #     'This is an abstract script. Users should subclass StreamParser in\n'
    #     'their own code and may then optionally call the main method of this\n'
    #     'script to invoke some basic command line parsing.')
    # exit(0)
