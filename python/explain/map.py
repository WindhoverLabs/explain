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

"""
The Map module contains the helper classes for looking at an ElfReader database.
"""
import os
from pprint import pprint
from typing import Any, Union, Optional

from explain.struct_fmt import struct_fmt

from explain.explain_error import ExplainError
from explain.sql import SQLiteCacheRow

__all__ = ['ElfMap', 'SymbolMap', 'FieldMap', 'BitFieldMap']


class ElfMap(SQLiteCacheRow):
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
            'SELECT id FROM symbols WHERE elf=? AND name NOT LIKE "\\_%" ESCAPE "\\"', (self.row,)).fetchall()
        for symbol in symbols:
            yield SymbolMap.from_cache(self.database, symbol[0])

    @classmethod
    def table(cls):
        return 'elfs'


class SymbolMap(SQLiteCacheRow):
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
    fields_by_name = ...  # type: dict[str, FieldMap]
    simple = ...  # type: SymbolMap
    SYMBOL_NAME_CACHE = {}

    def __init__(self, database, symbol_id):
        super().__init__(database, symbol_id)
        # These are technically immutable but for performance reasons that is
        # not enforced. Do not modify attributes of SymbolMap in user code
        # outside of this class without knowing exactly what you are doing.
        self.elf = ElfMap.from_cache(self.database, self['elf'])
        self.little_endian = self.elf['little_endian']
        # Cache SQL column to attributes
        self.byte_size = self['byte_size']
        # Symbol value format as seen by the struct module. Updated externally.
        self.fmt = None
        # Fields Cache
        self.fields = None
        self.fields_by_name = None
        self.refresh_field_cache()
        # Other properties.
        self.array = (0, None)
        """If not (0, None), this SymbolMap is an array of another SymbolMap.
        The value will otherwise be a 2-tuple, the 0th index is the size of the
        array, and the 1th index will be the SymbolMap that the array is of."""
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
            count = field0['multiplicity']
            field0_type = field0.type
            self.array = count, (field0_type if count != 0 else None)
            self.pointer = field0_type if field0.is_pointer else None
            self.is_base_type = self.pointer is not None
            self.typedef = field0_type if field0.is_typedef else None
            self.simple = field0_type.simple if self.typedef else self

        self.is_primitive = self.simple.is_base_type
        """True if this SymbolMap directly resolves to a base type through a
        chain of typedefs."""

    def __hash__(self):
        return hash((self.database, self.table(), self.row))

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
                    'SELECT id, name FROM symbols').fetchall()}
        symbol_id = SymbolMap.SYMBOL_NAME_CACHE[database][name]
        return SymbolMap.from_cache(database, symbol_id)

    def refresh_field_cache(self):
        c = self.database.execute(
            'SELECT id FROM fields WHERE symbol=? ORDER BY id', (self.row,))
        self.fields = [FieldMap.from_cache(self.database, field[0])
                       for field in c.fetchall()]
        self.fields_by_name = {field['name']: field for field in self.fields}

    def populate_cache(self):
        if self.fields is None:
            self.refresh_field_cache()

    @classmethod
    def table(cls):
        return 'symbols'


class FieldMap(SQLiteCacheRow):
    """A field of a Symbol. See the documentation of SymbolMap for how to
    interpret the prime field of a SymbolMap."""
    bit_field = ...  # type: BitFieldMap
    type = ...  # type:  Optional[SymbolMap]

    def __init__(self, database, row):
        super().__init__(database, row)
        self.bit_field = BitFieldMap.from_cache(self.database, self.row)
        self.byte_offset = self['byte_offset']
        self.is_pointer = self['name'] == '[pointer]'
        self.is_typedef = self['name'] == 'typedef'
        self.type = None
        field_type = self['type']
        if field_type is None:
            print('field {} is a null pointer.'.format(self.row))
            self.type = None
        elif self.is_pointer:
            self.type = None
        else:
            self.type = SymbolMap.from_cache(self.database, field_type)
        # self.type_simple = self.type.simple

    @property
    def pointer_type(self):
        if not self.is_pointer:
            raise ExplainError('This field is not a pointer.')
        return SymbolMap.from_cache(self.database, self['type'])

    @property
    def symbol(self):
        return SymbolMap.from_cache(self.database, self['symbol'])

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
