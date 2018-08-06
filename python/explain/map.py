"""
The Map module contains the helper classes for looking at an ElfReader database.
"""
import os

from explain.explain_error import ExplainError
from explain.sql import SQLiteCacheRow, SQLiteNamedRow

__all__ = ['ElfMap', 'SymbolMap', 'FieldMap', 'BitFieldMap']


class ElfMap(SQLiteNamedRow):
    """An ELF file. Can be used to find symbols in the ELF."""

    def __init__(self, database, row):
        """Extract an ELF from the database with row number."""
        super().__init__(database, row)

    @staticmethod
    def from_name(database, name):
        """Find ELF in database with a name and return it."""
        base_name = os.path.basename(name)
        elf_id = database.execute('SELECT id FROM elfs WHERE name==?',
                                  (base_name,)).fetchone()
        if elf_id is None:
            raise ExplainError('Cannot find ELF with file name {}'
                               .format(base_name))
        return ElfMap.from_cache(database, elf_id[0])

    def symbol(self, symbol_name):
        """Return symbol from ELF with name."""
        symbol_id = self.database.execute(
            'SELECT id FROM symbols WHERE elf=? AND name=?',
            (self.row, symbol_name)).fetchone()
        if symbol_id is None:
            raise ExplainError('There is no symbol with name {!r} in {!r}'
                               .format(symbol_name, self.name))
        return SymbolMap.from_cache(self.database, symbol_id[0])

    def symbols(self):
        """Yield all symbols in this ELF."""
        symbols = self.database.execute(
            'SELECT id FROM symbols WHERE elf=?', (self.row,)).fetchall()
        for symbol in symbols:
            yield SymbolMap.from_cache(self.database, symbol[0])

    @classmethod
    def table(cls):
        return 'elfs'


class SymbolMap(SQLiteNamedRow):
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
        super().__init__(database, symbol_id)
        self._field_cache = None

    @property
    def array(self):
        """Return the prime field if the Symbol is an array. Otherwise None.

        If given, the array type will be the type attribute of the prime field,
        and the count will be the multiplicity attribute.

        >>> array = SymbolMap().array
        >>> if array:
        ...     kind = array.type
        ...     count = array.multiplicity
        """
        try:
            field = self.fields()[0]
        except IndexError:
            return None
        return field if field['multiplicity'] != 0 else None

    @property
    def elf(self):
        return ElfMap.from_cache(self.database, self['elf'])

    def field(self, name):
        """Return the field of the Symbol with the given name."""
        if self._field_cache is None:
            self._fields_fill_cache()
        for field in self._field_cache:
            if field['name'] == name:
                return field
        raise KeyError("No field with name {!r} found.".format(name))

    def _fields_fill_cache(self):
        c = self.database.execute(
            'SELECT id FROM fields WHERE symbol=? ORDER BY id', (self.row,))
        self._field_cache = [FieldMap.from_cache(self.database, field[0])
                             for field in c.fetchall()]

    def fields(self):
        """Yields all of the fields in the Symbol."""
        if self._field_cache is None:
            self._fields_fill_cache()
        return self._field_cache

    @staticmethod
    def from_name(database, name):
        """Return a SymbolMap from the database with the given name.

        The ELF that the symbol came from is not guaranteed. Beware using this
        when different ELFs use different definitions of the same symbol name.

        To get a symbol from a specific ELF, use the preferred:
            >>> elf_map = ElfMap.from_name(database, 'elf.so')
            >>> symbol_map = elf_map.symbol(name)
        """
        symbol_id = database.execute('SELECT id FROM symbols WHERE name=?',
                                     (name,)).fetchone()[0]
        return SymbolMap.from_cache(database, symbol_id)

    @property
    def is_base_type(self):
        """Return True if the symbol is a base type.

        A base type is a symbol that cannot be decomposed into composite fields.
        It can either be a symbol with no fields, or a pointer.
        """
        fields = self.fields()
        return len(fields) == 0 or fields[0]['name'] == '[pointer]'

    @property
    def is_primitive(self):
        """Return True if the Symbol easily resolves to a base type.

        Easily resolves means that the symbol is a chain of typedef's
        to a base type.
        """
        return self.simple.is_base_type  # Note self.simple

    @property
    def pointer(self):
        """Return the prime field if the Symbol is a pointer. Otherwise None.

        If given, the type that is pointed to will be the type attribute of the
        prime field.

        >>> pointer = SymbolMap().pointer
        >>> if pointer:
        ...     points_at = pointer.type
        """
        try:
            field = self.fields()[0]
        except IndexError:
            return None
        return field if field['name'] == '[pointer]' else None

    @property
    def simple(self):
        """Follow typedefs and return the first symbol that is not a typedef."""
        if self.is_base_type or not self.typedef:
            return self
        # If here we can assume that it has fields. No try/catch required.
        return self.fields()[0].type.simple

    @classmethod
    def table(cls):
        return 'symbols'

    @property
    def typedef(self):
        """Return the prime field if the Symbol is a typedef. Otherwise None.

        If given, the type that the typedef is of will be the type attribute of
        the prime field.
        """
        try:
            field = self.fields()[0]
        except IndexError:
            return None
        return field if field['name'] == 'typedef' else None


class FieldMap(SQLiteNamedRow):
    """A field of a Symbol. See the documentation of SymbolMap for how to
    interpret the prime field of a SymbolMap."""

    def __init__(self, database, row):
        """Extract a field from the database with the given global row."""
        super().__init__(database, row)

    @property
    def bit_field(self):
        """Return the bit field if the field is a bit field, otherwise None."""
        field = self.database.execute('SELECT field FROM bit_fields WHERE '
                                      'field=?', (self.row,)).fetchone()
        return None if field is None else \
            BitFieldMap.from_cache(self.database, field[0])

    @classmethod
    def table(cls):
        return 'fields'

    @property
    def type(self):
        """Return what symbol the field contains."""
        return SymbolMap.from_cache(self.database, self['type'])


class BitFieldMap(SQLiteCacheRow):
    """A bit field for a field.

    Bit fields are uncommon optional parts of fields, so they are given a
    separate SQL table that references the associated field id.
    """
    _QUERY = 'SELECT {} FROM {} WHERE field=={}'

    def __init__(self, database, field_row):
        """Extract the bit field from the database that references the given
        field."""
        super(BitFieldMap, self).__init__(database, field_row)

    @classmethod
    def table(cls):
        return 'bit_fields'
