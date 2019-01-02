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


class UnknownMessageId(ExplainError):
    """Raised when a message ID is encountered that is unknown."""


class StreamCache(RawIOBase):
    """Caches stream output until cleared.

    Reads from the StreamCache are always performed from the start of the
    current cache, thus multiple reads of the same amount will return the same
    data as long as the cache has not been cleared.

    Currently unused. Feel free to delete.
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
            raise RuntimeError('Did not read enough bytes.')
        self.cache += read
        self.cache_len += len_read
        return self.cache


class StreamParser(SQLiteBacked, metaclass=ABCMeta):
    """Takes an IO stream (could be file or network) as input, and produces a
    stream of Symbols that are parsed from the input."""
    def __init__(self, database, stream):
        super(StreamParser, self).__init__(database)
        # TODO Add support for network streams (or any stream where not all of
        # it is available at once.
        self.stream = stream.read()

    @property
    @abstractmethod
    def data_offset(self):
        """Return the offset in bytes that the Symbol data starts in the
        stream."""
        return 0

    def read_symbol(self, symbol_map: SymbolMap, offset, little_endian=None):
        """Small helper method for reading a Symbol."""
        return Symbol(symbol_map, self.stream, offset, little_endian)

    @abstractmethod
    def structures(self, offset=0) -> Tuple[str, int]:
        """Yield the name and offset of each structure in the
        stream starting at offset."""
        raise NotImplementedError

    def parse(self):
        """Loop over the generated output from structures and yield each
        Symbol in the stream at that offset."""
        for name, offset in self.structures(offset=self.data_offset):
            yield self.read_symbol(
                symbol_map=SymbolMap.from_name(self.database, name),
                offset=offset)


class CcsdsMixin(StreamParser, metaclass=ABCMeta):
    """Mix this class in if the stream being parsed is a CCSDS stream.

    This class assumes that there is a CCSDS header at the start of every
    record, and each record structure begins at the same offset as the CCSDS
    header.

    This class uses ./ccsds_map.json to match StreamIds to structure names.
    """
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
            # Potential optimization: Eliminate read_symbol call and use the
            # struct module to simply parse out the StreamId and Length from the
            # raw bytes.
            offset += length
            ccsds = self.read_symbol(self.ccsds_map, offset=offset)
            try:
                stream_id, length = ccsds['StreamId'], ccsds['Length']
            except struct.error:
                return
            app_id = (stream_id[0].value << 8) + stream_id[1].value
            length = (length[0].value << 8) + length[1].value + 7
            try:
                yield self.msg_map[app_id], offset
            except KeyError:
                raise UnknownMessageId('App ID not recognized: ', hex(app_id))


class CfeStreamParser(StreamParser, metaclass=ABCMeta):
    """Assumes that the stream is a CFE stream, and looks for a CFE_FS_Header_t
    at the beginning of the stream."""
    def __init__(self, database, stream):
        super().__init__(database, stream)
        self.cfe_map = SymbolMap.from_name(self.database, 'CFE_FS_Header_t')
        self.cfe_header = self.read_symbol(
            self.cfe_map, offset=0, little_endian=False)

    @property
    def data_offset(self):
        return self.cfe_map['byte_size']


class AirlinerStreamParser(CfeStreamParser, CcsdsMixin):
    """Assumes that the stream is for an Airliner log, and assumes that there is
    a XX_FileHeader_t after the CFE header, where XX is the name of the App that
    created the log."""
    def __init__(self, database, stream, header_struct_name):
        super().__init__(database, stream)
        self.header_map = SymbolMap.from_name(self.database, header_struct_name)
        self.header = self.read_symbol(
            self.header_map, offset=self.cfe_map['byte_size'])

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
            #         return
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
