import argparse
import json
import os
import sqlite3
import struct
from abc import abstractmethod, ABCMeta
from collections import namedtuple, OrderedDict
from csv import writer
from io import RawIOBase
from time import time
from typing import Type, Dict, Tuple, Any, Union

from explain.explain_error import ExplainError
from explain.map import SymbolMap
from explain.elf_reader import ElfReader
from explain.sql import SQLiteBacked
from explain.symbol import Symbol


class EndOfStream(ExplainError, StopIteration):
    """Raised when a stream has been exhausted."""
    pass


class UnknownMessageId(ExplainError):
    """Raised when a message ID is encountered that is unknown."""


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
    def __init__(self, database, stream):
        super(StreamParser, self).__init__(database)
        self.stream = stream.read()

    @property
    @abstractmethod
    def data_offset(self):
        raise NotImplementedError

    def read_symbol(self, symbol_map: SymbolMap, offset, little_endian=None):
        return Symbol(symbol_map, self.stream, offset, little_endian)

    @abstractmethod
    def structures(self, offset=0) -> Tuple[str, int]:
        """Yield the name and offset of each structure in the
        stream starting at offset."""
        raise NotImplementedError

    def parse(self):
        for name, offset in self.structures(offset=self.data_offset):
            yield self.read_symbol(
                symbol_map=SymbolMap.from_name(self.database, name),
                offset=offset)


class CcsdsMixin(StreamParser, metaclass=ABCMeta):
    ccsds_map = ...  # type: SymbolMap
    msg_map = ...  # type: Dict[int, str]

    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.ccsds_map = SymbolMap.from_name(self.database, 'CCSDS_PriHdr_t')
        with open(os.path.join(
                os.path.dirname(__file__), 'ccsds_map.json')) as fp:
            self.msg_map = {int(k, 0): v for k, v in json.load(fp).items()}

    def structures(self, offset=0):
        length = 0
        while True:
            offset += length
            ccsds = self.read_symbol(self.ccsds_map, offset=offset)
            try:
                stream_id, length = ccsds['StreamId'], ccsds['Length']
            except struct.error:
                raise EndOfStream
            app_id = (stream_id[0].value << 8) + stream_id[1].value
            length = (length[0].value << 8) + length[1].value + 7
            try:
                yield self.msg_map[app_id], offset
            except KeyError:
                raise UnknownMessageId('App ID not recognized: ', hex(app_id))


class CfeStreamParser(StreamParser, metaclass=ABCMeta):
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.cfe_map = SymbolMap.from_name(self.database, 'CFE_FS_Header_t')
        self.cfe_header = self.read_symbol(
            self.cfe_map, offset=0, little_endian=False)

    @property
    def data_offset(self):
        return self.cfe_map['byte_size']


class AirlinerStreamParser(CfeStreamParser, CcsdsMixin):
    def __init__(self, database, stream, header_struct_name):
        super().__init__(database, stream)
        self.header_map = SymbolMap.from_name(self.database, header_struct_name)
        # self.header = self.read_symbol(
        #     self.header_map, offset=self.cfe_map['byte_size']
        # )

    @property
    def data_offset(self):
        return super(AirlinerStreamParser, self).data_offset \
               + self.header_map['byte_size']


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--database', default=':memory:',
                        help='database to read from')
    source.add_argument('--elf', help='ELF file to dynamically load')
    parser.add_argument('--csv', help='directory to put output csv files')
    parser.add_argument('stream', help='stream (file) to parse')
    parser.add_argument('file_struct', metavar='file-struct',
                        help='structure name that comes after '
                             'the CCSDS file header')

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

    stream_parser = AirlinerStreamParser(database, stream, args.file_struct)
    start_time = time()

    def prog(s):
        for n, p in enumerate(s):
            # if not n % 1000:
            #     print('{:6d}, {:.2f}'.format(n, time() - start_time))
            #     if n >= 30000:
            #         raise StopIteration
            yield p

    try:
        for symbol in prog(stream_parser.parse()):
            name = symbol.symbol_map['name']
            flat = OrderedDict(symbol.flatten())
            if name not in csvs:
                file = open(os.path.join(path, name + '.csv'), 'w')
                fieldnames = flat.keys()
                csv = writer(file)
                csv.writerow(fieldnames)
                csvs[name] = CsvFilePair(csv, file)
            csv = csvs[name].csv
            csv.writerow(flat.values())
    finally:
        for _, file in csvs.values():
            file.close()


if __name__ == '__main__':
    main()
    # print(
    #     'This is an abstract script. Users should subclass StreamParser in\n'
    #     'their own code and may then optionally call the main method of this\n'
    #     'script to invoke some basic command line parsing.')
    # exit(0)
