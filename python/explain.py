import argparse
import json
import os
import sqlite3
from collections import OrderedDict

from elf_reader import ElfReader


class ExplainError(Exception):
    """Base class for all Explain Errors."""
    pass


class SQLiteBacked(object):
    """An object that is represented by the contents of a database."""
    def __init__(self, database):
        self.database = database


class SQLiteRow(SQLiteBacked):
    """An object that is represented by a single row in a database.

    Provides helper methods for accessing columns/attributes of the row.
    """
    _QUERY = 'SELECT {} FROM {} WHERE id=={}'

    def __init__(self, database, table, row):
        """Construct object given the database, table name, and row number."""
        super().__init__(database)
        self.table = table
        if not isinstance(row, int):
            raise TypeError('Row primary key must be int. Got ' + repr(row))
        self.row = row

    def __getattr__(self, item):
        """If attribute is not found, fallback on database query for column."""
        try:
            return self.query1(item)
        except sqlite3.OperationalError:
            raise AttributeError(self.__class__.__name__ +
                                 ' has no attribute nor backing column ' +
                                 repr(item))

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(*c) for c in self.query('*')))

    def query(self, *columns):
        """Query columns from the row and return a list of column-value
        tuples."""
        cols = ', '.join(columns)
        c = self.database.execute(
            self._QUERY.format(cols, self.table, self.row))
        result = [(k[0], v) for k, v in zip(c.description, c.fetchone())]
        """:type: List[Tuple[str, Any]]"""
        return result

    def query1(self, column):
        """Query a single column and return only the value of the column."""
        return self.query(column)[0][1]


class Elf(SQLiteRow):
    """An ELF file. Can be used to find symbols in the ELF."""

    def __init__(self, database, row):
        """Extract an ELF from the database with row number."""
        super().__init__(database, 'elfs', row)

    @staticmethod
    def from_name(database, name):
        """Find ELF in database with a name and return it."""
        base_name = os.path.basename(name)
        elf_id = database.execute('SELECT id FROM elfs WHERE name==?',
                                  (base_name,)).fetchone()
        if elf_id is None:
            raise ExplainError('Cannot find ELF with file name {}'
                               .format(base_name))
        return Elf(database, elf_id[0])

    def symbol(self, symbol_name):
        """Return symbol from ELF with name."""
        symbol_id = self.database.execute(
            'SELECT id FROM symbols WHERE elf=? AND name=?',
            (self.row, symbol_name)).fetchone()
        if symbol_id is None:
            raise ExplainError('There is no symbol with name {!r} in {!r}'
                               .format(symbol_name, self.name))
        return Symbol(self.database, symbol_id[0])

    def symbols(self):
        """Yield all symbols in this ELF."""
        symbols = self.database.execute(
            'SELECT id FROM symbols WHERE elf=?', (self.row,)).fetchall()
        for symbol in symbols:
            yield Symbol(self.database, symbol[0])


class Symbol(SQLiteRow):
    """A symbol in an ELF. Symbols can be anything from structures to unions to
    base types.

    Symbols have fields that describe the data in the field. The first field is
    the prime field. Composite symbols contain at least one field, while base
    symbols (eg int, float) are identified by having no fields.

    Composite symbols are divided into kinds that determine what they represent.
    The name of the prime field determines if the symbol is one of the
    enumerated kinds below:
        'typedef' -> typedef to another Symbol
        '[pointer]' -> pointer to another Symbol
        '[array]' -> array of another Symbol

    If the composite symbol is not one of the enumerated kinds, it is either a
    struct, a union. Most user code will not actually make a strong distinction
    between structs and unions, though the identifying feature of unions is that
    all of their fields start at bit offset zero.

    Due to how the symbol is represented in the ELF/DWARF/DIE information, most
    of the information that identifies what the symbol is is exposed in the
    prime field of the symbol. Helper methods are provided to assist in the
    parsing of the fields.
    """
    def __init__(self, database, symbol_id):
        """Extract a symbol from the database with a global row number."""
        super().__init__(database, 'symbols', symbol_id)

    @property
    def array(self):
        """Return the prime field if the Symbol is an array. Otherwise None.

        If given, the array type will be the type attribute of the prime field,
        and the count will be the multiplicity attribute.

        >>> array = Symbol().array
        >>> if array:
        ...     kind = array.type
        ...     count = array.multiplicity
        """
        try:
            field = next(self.fields())
        except StopIteration:
            return None
        return field if field.multiplicity != 0 else None

    @property
    def is_base_type(self):
        """Return True if the symbol is a base type (ie has no fields)."""
        return len(list(self.fields())) == 0

    def fields(self):
        """Yields all of the fields in the Symbol."""
        c = self.database.execute(
            'SELECT id FROM fields WHERE symbol=? ORDER BY id', (self.row,))
        for field in c.fetchall():
            yield Field(self.database, field[0])

    @property
    def is_primitive(self):
        """Return True if the Symbol easily resolves to a base type.

        Easily resolves means that the symbol is a chain of typedef's
        to a base type.
        """
        return self.simple.is_base_type

    @property
    def pointer(self):
        """Return the prime field if the Symbol is a pointer. Otherwise None.

        If given, the type that is pointed to will be the type attribute of the
        prime field.

        >>> pointer = Symbol().pointer
        >>> if pointer:
        ...     points_at = pointer.type
        """
        try:
            field = next(self.fields())
        except StopIteration:
            return None
        return field if field.name == '[pointer]' else None

    @property
    def simple(self):
        """Follow typedefs and return the first symbol that is not a typedef."""
        if self.is_base_type or not self.typedef:
            return self
        return next(self.fields()).type.simple

    @property
    def typedef(self):
        """Return the prime field if the Symbol is a typedef. Otherwise None.

        If given, the type that the typedef is of will be the type attribute of
        the prime field.
        """
        try:
            field = next(self.fields())
        except StopIteration:
            return None
        return field if field.name == 'typedef' else None


class Field(SQLiteRow):
    """A field of a Symbol. See the documentation of Symbol for how to interpret
    the prime field of a Symbol."""

    def __init__(self, database, row):
        """Extract a field from the database with the given global row."""
        super().__init__(database, 'fields', row)

    @property
    def bit_field(self):
        """Return the bit field if the field is a bit field, otherwise None."""
        field = self.database.execute('SELECT field FROM bit_fields WHERE '
                                      'field=?', (self.row,)).fetchone()
        return None if field is None else BitField(self.database, field[0])

    @property
    def type(self):
        """Return what symbol the field contains."""
        return Symbol(self.database, self.query1('type'))


class BitField(SQLiteRow):
    """A bit field for a field.

    Bit fields are uncommon optional parts of fields, so they are given a
    separate SQL table that references the associated field id.
    """
    _QUERY = 'SELECT {} FROM {} WHERE field=={}'

    def __init__(self, database, field_row):
        """Extract the bit field from the database that references the given
        field."""
        super(BitField, self).__init__(database, 'bit_fields', field_row)


def json_symbol(symbol):
    def field(f):
        fd = OrderedDict()
        fd['name'] = f.name
        # fd['type'] = f.type.name
        bit_field = f.bit_field
        fd['bit_offset'] = f.byte_offset * 8
        if not bit_field:
            fd['bit_size'] = f.type.byte_size * 8
        else:
            fd['bit_offset'] += bit_field.bit_offset
            fd['bit_size'] = bit_field.bit_size
        kind = f.type  # type: Symbol
        array = kind.array
        simple = kind.simple  # type: Symbol
        if array is not None:
            fd['array'] = True
            fd['count'] = array.multiplicity
            fd['kind'] = json_symbol(array.type.simple)
        elif not simple.is_base_type and not kind.pointer:
            fd['fields'] = [field(f) for f in simple.fields()]

        # pointer = symbol.pointer
        # fd['type'] = pointer.name if pointer else json_symbol(field.type)
        return fd

    s = OrderedDict()
    s['name'] = symbol.name
    s['bit_size'] = symbol.byte_size * 8
    if not symbol.pointer and not symbol.is_primitive:
        s['fields'] = None if symbol.is_base_type else \
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
    parser.add_argument('file', help='ELF file from the database')
    # parser.add_argument('--cache')
    parser.add_argument('--database', default=':memory:',
                        help='use an existing database')
    parser.add_argument('--load', action='store_true',
                        help='load a new ELF file if an existing database is '
                             'chosen')
    parser.add_argument('--out', help='output json file')
    parser.add_argument('--print', help='print selected symbol(s)')
    parser.add_argument('--reentrant', action='store_true',
                        help='ignore any duplicate ELFs')
    symbol = parser.add_mutually_exclusive_group(required=True)
    symbol.add_argument('-a', '--all', action='store_true',
                        help='output all symbols')
    symbol.add_argument('symbol', nargs='?', help='the symbol name to look at')

    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    if args.database == ':memory:' or args.load:
        quenya = ElfReader(db)
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
