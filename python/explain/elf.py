import os

from explain.explain_error import ExplainError
from explain.sql import SQLiteRow


__all__ = ['Elf', 'Symbol', 'Field', 'BitField']


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