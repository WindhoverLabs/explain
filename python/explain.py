import argparse
import os
import sqlite3

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
                                 'nor backing column ' + repr(item))

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
        return field.multiplicity

    @property
    def base_type(self):
        return len(list(self.fields())) == 0

    def fields(self):
        c = self.database.execute(
            'SELECT id FROM fields WHERE symbol=? ORDER BY id', (self.row,))
        for field in c.fetchall():
            yield Field(self.database, field[0])

    def print_tree(self, level=0, max_level=float('inf')):
        if level > max_level:
            return
        indstr = '| '
        indent = indstr * level
        print('{}symbol {} size={}'.format(indent, self.name, self.byte_size))
        if self.base_type:
            return
        indent = indstr * (level + 1)
        typedef = self.typedef
        array = self.array
        if typedef:
            return typedef.print_tree(level + 1, max_level=max_level)
        if array:
            # TODO do array things
            pass
        for field in self.fields():
            print('{}field {} {} x{}'.format(
                indent, field.byte_offset, field.name, field.multiplicity))
            if field.name != '[pointer]':
                field.type.print_tree(level + 2, max_level=max_level)

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


def main():
    parser = argparse.ArgumentParser(
        description='Searches a Quenya database for a symbol.')
    # parser.add_argument('--cache')
    parser.add_argument('--database', default=':memory:',
                        help='use an existing database')
    parser.add_argument('--load', action='store_true',
                        help='load a new ELF file if an existing database is '
                             'chosen')
    parser.add_argument('--reentrant', action='store_true',
                        help='ignore any duplicate ELFs')
    parser.add_argument('file', help='ELF file from the database')
    symbol = parser.add_mutually_exclusive_group(required=True)
    symbol.add_argument('-a', '--all', action='store_true',
                        help='output all symbols')
    symbol.add_argument('--symbol', help='the symbol name to look at')

    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    if args.database == ':memory:' or args.load:
        quenya = Quenya(db)
        quenya.insert_elf(args.file)

    elf = Elf.from_name(db, args.file)
    symbols = (elf.symbol(symbol_name=args.symbol),) if not args.all else \
        elf.symbols()
    for symbol in symbols:
        symbol.print_tree()


if __name__ == '__main__':
    main()
