"""
The Map module contains the helper classes for looking at an ElfReader database.
"""
import os
from typing import Any, Union, Optional

from explain.explain_error import ExplainError
from explain.sql import SQLiteCacheRow, SQLiteNamedRow
from explain.struct_fmt import struct_fmt

__all__ = ['ElfMap', 'SymbolMap', 'FieldMap', 'BitFieldMap']


class ElfMap(SQLiteNamedRow):
    """An ELF file. Can be used to find symbols in the ELF."""

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

    SymbolMaps are immutable, but this is not enforced for performance reasons.
    Do not reassign attributes outside of the constructor without knowing
    exactly what ramifications it may have.
    """
    array = ...  # type: Optional[FieldMap]
    fields = ...  # type: list[FieldMap]
    _fields_by_name = ...  # type: dict[str, FieldMap]
    simple = ...  # type: SymbolMap
    SYMBOL_NAME_CACHE = {}

    def __init__(self, database, symbol_id):
        super().__init__(database, symbol_id)
        # These are technically immutable but for performance reasons that is
        # not enforced. Do not modify in user code outside of this class.
        self.elf = ElfMap.from_cache(self.database, self['elf'])
        self.little_endian = self.elf['little_endian']
        # Fields Cache
        self.fields = None
        self._fields_by_name = None
        self._refresh_cache()
        # Other properties.
        self.array = None
        """If not None, this SymbolMap is an array of another SymbolMap. The
        value will be the FieldMap for the array."""
        self.is_base_type = True
        """A base type is a symbol that cannot be decomposed into composite 
        fields. It can either be a symbol with no fields, or a pointer."""
        self.pointer = None
        """If not None, this SymbolMap is a pointer, and the value is a
        SymbolMap to the type represented by the pointer."""
        self.simple = self
        """The next SymbolMap moving up the type hierarchy that is not a
        typedef. Is `self` if `self.is_base_type`."""
        self.typedef = None
        """If not None, this SymbolMap is a typedef to another type. The value
        will be the SymbolMap that it is typedef'd to."""

        if bool(self.fields):
            field0 = self.fields[0]
            self.array = field0 if field0['multiplicity'] != 0 else None
            self.is_base_type = field0['name'] == '[pointer]'
            self.pointer = field0.type if field0['name'] == '[pointer]' else None
            self.typedef = field0.type if field0['name'] == 'typedef' else None
            self.simple = field0.type.simple if self.typedef else self

        self.is_primitive = self.simple.is_base_type
        """True if this SymbolMap directly resolves to a base type through a
        chain of typedefs."""
        self.fmt = None

    def __hash__(self):
        return hash((self.database, self.table(), self.row))

    def field(self, name):
        """Return the field of the Symbol with the given name."""
        return self._fields_by_name[name]

    def _refresh_cache(self):
        c = self.database.execute(
            'SELECT id FROM fields WHERE symbol=? ORDER BY id', (self.row,))
        self.fields = [FieldMap.from_cache(self.database, field[0])
                       for field in c.fetchall()]
        self._fields_by_name = {field['name']: field for field in self.fields}

    @staticmethod
    def from_name(database, name):
        """Return a SymbolMap from the database with the given name.

        The ELF that the symbol came from is not guaranteed. Beware using this
        when different ELFs use different definitions of the same symbol name.

        To get a symbol from a specific ELF, use the preferred:
            >>> elf_map = ElfMap.from_name(database, 'elf.so')
            >>> symbol_map = elf_map.symbol(name)
        """
        # Build name->id index in memory.
        if database not in SymbolMap.SYMBOL_NAME_CACHE:
            SymbolMap.SYMBOL_NAME_CACHE[database] = {
                name: symbol_id for symbol_id, name in database.execute(
                    'SELECT id, name FROM symbols').fetchall()
            }
        symbol_id = SymbolMap.SYMBOL_NAME_CACHE[database][name]
        return SymbolMap.from_cache(database, symbol_id)

    @classmethod
    def table(cls):
        return 'symbols'


class FieldMap(SQLiteNamedRow):
    """A field of a Symbol. See the documentation of SymbolMap for how to
    interpret the prime field of a SymbolMap."""
    bit_field = ...  # type: BitFieldMap
    type = ...  # type: SymbolMap

    def __init__(self, database, row):
        super().__init__(database, row)
        self.bit_field = BitFieldMap.from_cache(self.database, self.row)
        self.type = SymbolMap.from_cache(self.database, self['type'])

    @classmethod
    def table(cls):
        return 'fields'


class BitFieldMap(SQLiteCacheRow):
    """A bit field for a field.

    Bit fields are uncommon optional parts of fields, so they are given a
    separate SQL table that references the associated field id.
    """
    _QUERY = 'SELECT {} FROM {} WHERE field=={}'
    BIT_FIELD_CACHE = {}

    @classmethod
    def from_cache(cls, database, row):
        if database not in BitFieldMap.BIT_FIELD_CACHE:
            BitFieldMap.BIT_FIELD_CACHE[database] = [
                row[0] for row in database.execute(
                    'SELECT field FROM bit_fields').fetchall()]
        if row in BitFieldMap.BIT_FIELD_CACHE[database]:
            return super(BitFieldMap, cls).from_cache(database, row)

    @classmethod
    def table(cls):
        return 'bit_fields'
