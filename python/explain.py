import argparse
import json
import os
import sqlite3
from collections import OrderedDict
from typing import Any, Union

from quenya import Quenya


class ExplainError(Exception):
    pass


class SQLiteBacked(object):
    def __init__(self, database):
        self.database = database


class SQLiteRow(SQLiteBacked):
    def __init__(self, database, table, row):
        super().__init__(database)
        self.table = table
        if not isinstance(row, int):
            raise TypeError('Row primary key must be int. Got ' + repr(row))
        self.row = row

    def __getattr__(self, item):
        try:
            return self.query1(item)
        except sqlite3.OperationalError:
            raise AttributeError(self.__class__.__name__ + ' has no attribute '
                                                           'nor backing column ' + repr(
                item))

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(*c) for c in self.query('*')))

    def query(self, *columns):
        """Query columns from the row and return a list of column-value
        tuples."""
        cols = ', '.join(columns)
        c = self.database.execute(
            'SELECT {} FROM {} WHERE id=={}'.format(cols, self.table, self.row))
        result = [(k[0], v) for k, v in zip(c.description, c.fetchone())]
        """:type: List[Tuple[str, Any]]"""
        return result

    def query1(self, column):
        """Query a single column and return only the value of the column."""
        return self.query(column)[0][1]


class Elf(SQLiteRow):
    def __init__(self, database, row):
        super().__init__(database, 'elfs', row)

    @staticmethod
    def from_name(database, name):
        base_name = os.path.basename(name)
        elf_id = database.execute('SELECT id FROM elfs WHERE name==?',
                                  (base_name,)).fetchone()
        if elf_id is None:
            raise ExplainError('Cannot find ELF with file name {}'
                               .format(base_name))
        return Elf(database, elf_id[0])

    def symbol(self, symbol_name):
        symbol_id = self.database.execute(
            'SELECT id FROM symbols WHERE elf=? AND name=?',
            (self.row, symbol_name)).fetchone()
        if symbol_id is None:
            raise ExplainError('There is no symbol with name {!r} in {!r}'
                               .format(symbol_name, self.name))
        return Symbol(self.database, symbol_id[0])

    def symbols(self):
        symbols = self.database.execute(
            'SELECT id FROM symbols WHERE elf=?', (self.row,)).fetchall()
        for symbol in symbols:
            yield Symbol(self.database, symbol[0])


class Symbol(SQLiteRow):
    def __init__(self, database, symbol_id=None):
        super().__init__(database, 'symbols', symbol_id)

    @property
    def array(self):
        try:
            field = next(self.fields())
        except StopIteration:
            return None
        return field if field.multiplicity != 0 else None

    @property
    def base_type(self):
        return len(list(self.fields())) == 0

    def fields(self):
        c = self.database.execute(
            'SELECT id FROM fields WHERE symbol=? ORDER BY id', (self.row,))
        for field in c.fetchall():
            yield Field(self.database, field[0])

    @property
    def is_primitive(self):
        return self.simple.base_type

    @property
    def pointer(self):
        try:
            field = next(self.fields())
        except StopIteration:
            return None
        return field.type if field.name == '[pointer]' else None

    @property
    def simple(self):
        """Follow typedefs and return a base type or a complex type.

        A complex type is a type that cannot be represented as a single unit,
        such as a struct or union.
        """
        print(self.name, list(self.fields()))
        if self.base_type or len(list(self.fields())) > 1:
            return self
        return next(self.fields()).type.simple

    @property
    def typedef(self):
        try:
            field = next(self.fields())
        except StopIteration:
            return None
        if field.name == 'typedef':
            return field.type
        return None


class Field(SQLiteRow):
    def __init__(self, database, row):
        super().__init__(database, 'fields', row)

    @property
    def bit_field(self):
        field = self.database.execute('SELECT field FROM bit_fields WHERE '
                                      'field=?', (self.row,)).fetchone()
        return None if field is None else BitField(self.database, field[0])

    @property
    def type(self):
        return Symbol(self.database, self.query1('type'))


class BitField(SQLiteRow):
    def __init__(self, database, row):
        super(BitField, self).__init__(database, 'bit_fields', row)


def json_symbol(symbol):
    def field(f):
        fd = OrderedDict()
        fd['name'] = f.name
        # fd['type'] = f.type.name
        fd['bit_offset'] = f.byte_offset * 8
        fd['bit_size'] = f.type.byte_size * 8
        kind = f.type  # type: Symbol
        array = kind.array
        if array:
            # TODO flesh out arrays
            fd['array'] = True
            fd['count'] = array.multiplicity
            fd['kind'] = json_symbol(array.type.simple)
        simple = kind.simple  # type: Symbol
        # fd['simple'] = simple.name
        if not simple.base_type:
            fd['fields'] = [field(f) for f in simple.fields()]

        # pointer = symbol.pointer
        # fd['type'] = pointer.name if pointer else json_symbol(field.type)
        return fd

    s = OrderedDict()
    s['name'] = symbol.name
    s['bit_size'] = symbol.byte_size * 8
    if not symbol.pointer and not symbol.is_primitive:
        s['fields'] = None if symbol.base_type else \
            [field(f) for f in symbol.fields()]
    return s


def json_output(file_stream, elf, symbols):
    out = OrderedDict()
    out['file'] = elf.name
    out['little_endian'] = elf.little_endian == 1
    out['symbols'] = [json_symbol(s) for s in symbols]
    json.dump(out, file_stream, indent='  ')


def main():
    parser = argparse.ArgumentParser(
        description='Searches a Quenya database for a symbol.')
    # parser.add_argument('--cache')
    symbol = parser.add_mutually_exclusive_group(required=True)
    symbol.add_argument('-a', '--all', action='store_true',
                        help='output all symbols')
    parser.add_argument('--database', default=':memory:',
                        help='use an existing database')
    parser.add_argument('--load', action='store_true',
                        help='load a new ELF file if an existing database is '
                             'chosen')
    parser.add_argument('--out', help='output json file')
    parser.add_argument('--print', help='print selected symbol(s)')
    parser.add_argument('--reentrant', action='store_true',
                        help='ignore any duplicate ELFs')
    symbol.add_argument('--symbol', help='the symbol name to look at')
    parser.add_argument('file', help='ELF file from the database')

    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    if args.database == ':memory:' or args.load:
        quenya = Quenya(db)
        quenya.insert_elf(args.file)

    elf = Elf.from_name(db, args.file)
    symbols = (elf.symbol(symbol_name=args.symbol),) if not args.all else \
        elf.symbols()
    if args.print:
        for symbol in symbols:
            symbol.print_tree()

    if args.out:
        with open(args.out, 'w') as fp:
            json_output(fp, elf, symbols)


if __name__ == '__main__':
    main()
