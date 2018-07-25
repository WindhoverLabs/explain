"""
Quenya is a tool for parsing the DWARF and DIE sections of an ELF file.

Code Limitations:
    ELF files to be parsed must conform to the following requirements:
    1. All relevant typedefs, structs, and unions must be defined in the top-
        level of a file. Quenya will not look inside function or namespace
        definitions.
    2. Things which are typedef'd must have either the same tag as
        their typedef or be untagged.
        ie, "typedef struct A { int x; } B;" is disallowed.
"""

import argparse
import hashlib
import logging
import os
import sqlite3
import sys
from logging import Logger

from elftools.elf.elffile import ELFFile

from loggable import Loggable


class QuenyaError(Exception):
    """Base type for Quenya Errors."""


class Quenya(Loggable):
    """Quenya: the language of the High Elves"""

    def __init__(self, database, logger: Logger = None) -> None:
        super().__init__(logger)
        self.database = database
        self.create_tables()

    @staticmethod
    def checksum(file_name, block_size=8192):
        """Return the checksum of the file at file_name.

        The name of the algorithm is prepended to the checksum digest.
        """
        check = hashlib.md5()
        with open(file_name, 'rb') as fp:
            while True:
                chunk = fp.read(block_size)
                if not chunk:
                    break
                check.update(chunk)
        return b'md5' + check.digest()

    def create_tables(self):
        c = self.database.cursor()
        c.execute(
            'CREATE TABLE IF NOT EXISTS elfs ('
            'id INTEGER PRIMARY KEY,'
            'name TEXT NOT NULL,'
            'checksum TEXT NOT NULL,'
            'date DATETIME NOT NULL DEFAULT(CURRENT_TIMESTAMP),'
            'little_endian BOOLEAN NOT NULL,'
            'UNIQUE (name, checksum)'
            ');')
        c.execute(
            'CREATE TABLE IF NOT EXISTS symbols ('
            'id INTEGER PRIMARY KEY,'
            'elf INTEGER NOT NULL,'
            'name TEXT NOT NULL,'
            'byte_size INTEGER NOT NULL,'
            'FOREIGN KEY(elf) REFERENCES elfs(id),'
            'UNIQUE (elf, name)'
            ')')
        c.execute(
            'CREATE TABLE IF NOT EXISTS fields('
            'id INTEGER PRIMARY KEY,'
            'symbol INTEGER NOT NULL,'
            'name TEXT NOT NULL,'
            'byte_offset INTEGER NOT NULL,'
            'type INTEGER,'
            'multiplicity INTEGER NOT NULL,'
            'FOREIGN KEY (symbol) REFERENCES symbols(id),'
            'FOREIGN KEY (type) REFERENCES symbols(id),'
            'UNIQUE (symbol, name)'
            ')')
        c.execute(
            'CREATE TABLE IF NOT EXISTS bit_fields('
            'field INTEGER PRIMARY KEY,'
            'bit_size INTEGER NOT NULL,'
            'bit_offset INTEGER NOT NULL,'
            'FOREIGN KEY (field) REFERENCES fields(id)'
            ') WITHOUT ROWID')
        c.execute(
            'CREATE TABLE IF NOT EXISTS enumerations('
            'id INTEGER PRIMARY KEY,'
            'symbol INTEGER NOT NULL,'
            'value INTEGER NOT NULL,'
            'name TEXT NOT NULL,'
            'FOREIGN KEY (symbol) REFERENCES symbols(id),'
            'UNIQUE (symbol, value)'
            ')')
        c.close()

    @property
    def dump(self):
        return '\n'.join(line for line in self.database.iterdump())

    def insert_elf(self, file_name):
        """Insert an ELF file and symbols into Elvish. True if successful."""
        # Checksum and load ELF
        try:
            stream = open(file_name, 'rb')
        except FileNotFoundError:
            print('No such file: {!r}'.format(file_name))
            return False
        elf = ELFFile(stream)
        checksum = self.checksum(file_name)
        base = os.path.basename(file_name)

        # Insert ELF file into elfs table.
        c = self.database.cursor()
        try:
            # Note: sqlite does not store binary data. Must use sqlite.Binary
            # to pass in checksum.
            c.execute('INSERT INTO elfs(name, checksum, little_endian) '
                      'VALUES (?, ?, ?)',
                      (base, sqlite3.Binary(checksum), elf.little_endian))
        except sqlite3.IntegrityError:
            c.execute('SELECT date FROM elfs WHERE name=? AND checksum=?',
                      (base, sqlite3.Binary(checksum)))
            duplicate = c.fetchone()
            raise QuenyaError('{!r} matched previously loaded ELF uploaded on '
                              '{}'.format(base, duplicate[0]))

        # Insert symbols from ELF
        elf_id = c.lastrowid
        elf_view = ElfView(self.database, elf_id, self.logger)
        elf_view.insert_symbols_from_elf(elf)
        return True


class ElfView(Loggable):
    ENCODING = 'utf-8'

    def __init__(self, database, elf_id, logger=None):
        super().__init__(logger)
        self.database = database
        self.elf_id = elf_id

    def insert_bit_field(self, field_id, bit_size, bit_offset):
        self.debug('insert_bit_field({!r}, {}, {})'.format(
            field_id, bit_size, bit_offset))
        c = self.database.cursor()
        c.execute('INSERT INTO bit_fields(field, bit_size, bit_offset) VALUES '
                  '(?, ?, ?)', (field_id, bit_size, bit_offset))
        c.close()

    def insert_enumeration(self, symbol_id, value, name):
        self.debug('insert_enumeration({!r}, {}, {})'.format(
            symbol_id, value, name))
        c = self.database.cursor()
        enum_id = c.execute('SELECT id FROM enumerations WHERE symbol=? AND '
                            'value=?', (symbol_id, value)).fetchone()
        if enum_id is None:
            c.execute('INSERT INTO enumerations(symbol, value, name) '
                      'VALUES (?, ?, ?)', (symbol_id, value, name))
            enum_id = c.lastrowid
        else:
            enum_id = enum_id[0]
        c.close()
        return enum_id

    def insert_field(self, symbol_id, name, byte_offset, kind, multiplicity=0,
                     allow_void=False):
        self.debug('insert_field({!r}, {}, {}, {})'.format(
            symbol_id, name, byte_offset, kind, multiplicity))
        if kind is None and not allow_void:
            raise QuenyaError('Attempted to add a void field type without '
                              'explicit override.')
        c = self.database.cursor()
        c.execute('INSERT INTO fields(symbol, name, byte_offset, type,'
                  'multiplicity) VALUES (?, ?, ?, ?, ?)',
                  (symbol_id, name, byte_offset, kind, multiplicity))
        field_id = c.lastrowid
        c.close()
        return field_id

    def insert_symbol(self, name, byte_size):
        """Insert a symbol with name and byte_size."""
        self.debug('insert_symbol({!r}, byte_size={})'.format(
            name, byte_size))
        c = self.database.cursor()
        c.execute('INSERT INTO symbols(elf, name, byte_size)'
                  'VALUES(?, ?, ?)', (self.elf_id, name, byte_size))
        symbol_id = c.lastrowid
        c.close()
        return symbol_id

    def field(self, symbol_id, name):
        c = self.database.cursor()
        field_id = c.execute('SELECT id FROM fields WHERE symbol=? AND name=?',
                             (symbol_id, name)).fetchone()
        c.close()
        return field_id[0] if field_id is not None else None

    def symbol(self, name):
        c = self.database.cursor()
        symbol_id = c.execute('SELECT id FROM symbols WHERE elf=? AND '
                              'name=?', (self.elf_id, name)).fetchone()
        c.close()
        return symbol_id[0] if symbol_id is not None else None

    def insert_symbols_from_elf(self, elf):
        # print(elf.header)
        dwarf = elf.get_dwarf_info()

        for i, cu in enumerate(dwarf.iter_CUs()):
            self.debug('CU #{}: {}'.format(i, cu.header))
            top = cu.get_top_DIE()
            dies = {c.offset - cu.cu_offset: c for c in top.iter_children()}
            self.cu_offset = cu.cu_offset

            for child in top.iter_children():
                self._symbol_requires(dies, child.offset - self.cu_offset)

    def _symbol_requires(self, dies, die_offset, typedef=None):
        self.debug('_symbol_requires 0x{:x} (typedef={!r})'.format(
            die_offset, typedef))
        try:
            symbol = dies[die_offset]
        except KeyError:
            # Find possible enclosing tag
            closest = sorted(filter(lambda k: k < die_offset, dies.keys()))[-1]
            self.exception(
                'Could not locate DIE at 0x{:x}. The previous tag that Quenya '
                'recognizes is a {} at 0x{:x}.'
                    .format(die_offset, dies[closest].tag, closest))
            return None
        if isinstance(symbol, int):
            self.debug('Found inserted symbol id = {}'.format(symbol))
            return symbol
        known_tags = {
            'DW_TAG_array_type': self._tag_array_type,
            'DW_TAG_base_type': self._tag_base_type,
            'DW_TAG_enumeration_type': self._tag_enumeration_type,
            'DW_TAG_pointer_type': self._tag_pointer_type,
            'DW_TAG_structure_type': self._tag_structure_type,
            'DW_TAG_typedef': self._tag_typedef,
            'DW_TAG_union_type': self._tag_union_type,
            # Known Skipped Tags
            'DW_TAG_class_type': self._tag_skip,
            'DW_TAG_const_type': self._tag_skip,
            'DW_TAG_imported_module': self._tag_skip,
            'DW_TAG_namespace': self._tag_skip,
            'DW_TAG_reference_type': self._tag_skip,
            'DW_TAG_rvalue_reference_type': self._tag_skip,
            'DW_TAG_restrict_type': self._tag_skip,
            'DW_TAG_subprogram': self._tag_skip,
            'DW_TAG_subroutine_type': self._tag_skip,
            'DW_TAG_unspecified_type': self._tag_skip,
            'DW_TAG_variable': self._tag_skip,
        }
        try:
            callback = known_tags[symbol.tag]
        except KeyError as e:
            raise QuenyaError(
                'symbol_requires can\'t handle {} at DIE 0x{:x}\n{}'
                    .format(symbol.tag, die_offset, symbol)) from e
        return callback(dies, symbol.offset, typedef=typedef)

    def _die_byte_size(self, die_offset):
        """Get the byte size of a DIE."""
        self.debug('_die_byte_size {}'.format(str(die_offset)[:20]))
        if isinstance(die_offset, int):
            c = self.database.cursor()
            c.execute('SELECT byte_size FROM symbols WHERE id=?', (die_offset,))
            size = c.fetchone()[0]
            c.close()
        else:
            tag = die_offset.tag
            if tag == 'DW_TAG_base_type':
                size = die_offset.attributes['DW_AT_byte_size'].value
            else:
                raise QuenyaError('Can\'t get size of {} at DIE 0x{:x}'.format(
                    tag, die_offset))
        return size

    def _tag_array_type_multiplicity(self, die, die_offset):
        multiplicity = None
        for child in die.iter_children():
            if child.tag == 'DW_TAG_subrange_type':
                upper_bound = child.attributes['DW_AT_upper_bound'].value
                if not isinstance(upper_bound, int):
                    self.warning(
                        'Array with unknown length declared at DIE 0x{:x}'
                            .format(die_offset))
                    return -1
                length = upper_bound + 1
                if multiplicity is None:
                    multiplicity = length
                else:
                    multiplicity *= length
            else:
                raise QuenyaError('Unknown array child at:\n' + str(die))
        return multiplicity

    def _tag_array_type(self, dies, die_offset, typedef=None):
        """Insert an array."""
        self.debug('_tag_array_type 0x{:x}'.format(die_offset))
        die = dies[die_offset - self.cu_offset]
        array_type = die.attributes['DW_AT_type'].value
        array_type_id = self._symbol_requires(dies, array_type)
        if array_type_id is None:
            self.warning('Skipping array of unknown type at DIE 0x{:x}'
                         .format(die_offset))
            return None
        c = self.database.cursor()
        c.execute('SELECT name, byte_size FROM symbols WHERE id=?',
                  (array_type_id,))
        array_type_name, unit_byte_size = c.fetchone()
        c.close()
        multiplicity = self._tag_array_type_multiplicity(die, die_offset)
        array_name = 'array_{}_{}'.format(array_type_name, multiplicity)
        symbol_size = unit_byte_size * multiplicity
        symbol_id = self.symbol(array_name)
        if symbol_id is not None:
            # Symbol exists
            return symbol_id
        symbol_id = self.insert_symbol(array_name, symbol_size)
        self.insert_field(symbol_id, '[array]', 0, array_type_id, multiplicity)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_base_type(self, dies, die_offset, typedef=None):
        """Insert a base type."""
        self.debug('_tag_base_type 0x{:x}'.format(die_offset))
        die = dies[die_offset - self.cu_offset]
        name = die.attributes['DW_AT_name'].value.decode(ElfView.ENCODING)
        size = die.attributes['DW_AT_byte_size'].value
        symbol_id = self.symbol(name) or self.insert_symbol(name, size)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_enumeration_type(self, dies, die_offset, typedef=None):
        """Insert an enumeration."""
        self.debug('_tag_enumeration_type 0x{:x}'.format(die_offset))
        die = dies[die_offset - self.cu_offset]
        if not typedef:
            self.debug('Skipping direct enum at 0x{:x}'.format(
                die_offset))
            return
        symbol_name = typedef
        symbol_byte_size = die.attributes['DW_AT_byte_size'].value
        symbol_id = self.symbol(symbol_name) \
                    or self.insert_symbol(symbol_name, symbol_byte_size)
        for child in die.iter_children():
            cname = child.attributes['DW_AT_name'] \
                .value.decode(ElfView.ENCODING)
            cvalue = child.attributes['DW_AT_const_value'].value
            self.insert_enumeration(symbol_id, cvalue, cname)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_skip(self, dies, die_offset, typedef=None):
        """Skip over the known tag.

        Unknown tags will raise a KeyError in symbol_requires.
        """
        tag = dies[die_offset - self.cu_offset].tag
        self.debug(
            'Skipping known tag {} at 0x{:x} (typedef={!r})'
                .format(tag, die_offset, typedef))

    def _tag_structure_type(self, dies, die_offset, typedef=None):
        """Insert a structure."""
        self.debug('_tag_structure_type 0x{:x}'.format(die_offset))
        return self._tag_structure_or_union_type(
            dies, die_offset, typedef=typedef, union=False)

    def _tag_structure_or_union_type(self, dies, die_offset, union,
                                     typedef=None):
        """Insert a struct or a union.

        Structs and unions have very similar DIE structures which is why these
        two are combined.
        """
        kind = 'union' if union else 'structure'
        die = dies[die_offset - self.cu_offset]
        try:
            symbol_name = die.attributes['DW_AT_name'] \
                .value.decode(ElfView.ENCODING)
        except KeyError:
            # Unnamed structure. typedef must be set to continue.
            if not typedef:
                self.debug('Skipping unnamed {} at 0x{:x}'.format(
                    kind, die_offset))
                return None
            symbol_name = typedef
        try:
            byte_size = die.attributes['DW_AT_byte_size'].value
        except KeyError:
            # Weird structs with no size deserve to be skipped.
            self.exception('{} has no size at DIE 0x{:x}'
                           .format(kind, die_offset))
            return None
        symbol_id = self.symbol(symbol_name)
        if symbol_id is not None:
            # Already exists.
            return symbol_id
        symbol_id = self.insert_symbol(symbol_name, byte_size)
        # Have to replace DIE lookup here in case of recursive struct.
        dies[die_offset - self.cu_offset] = symbol_id
        for child in die.iter_children():
            if child.tag == 'DW_TAG_member':
                try:
                    field_name = child.attributes['DW_AT_name'] \
                        .value.decode(ElfView.ENCODING)
                except KeyError:
                    self.exception('Skipping field with no name at '
                                   'DIE 0x{:x}'.format(child.offset))
                    continue
                self.debug('{} {}.{}'
                           .format(kind, symbol_name, field_name))
                byte_offset = 0 if union else \
                    child.attributes['DW_AT_data_member_location'].value
                field_type = child.attributes['DW_AT_type'].value
                field_type_id = self._symbol_requires(
                    dies, field_type, typedef=field_name)
                if field_type_id is None:
                    self.warning(
                        'Skipping field {} with unknown type at DIE 0x{:x}'
                            .format(field_name, die_offset))
                    continue
                field_id = self.insert_field(
                    symbol_id, field_name, byte_offset, field_type_id)
                # Insert bit field entry if appropriate.
                if 'DW_AT_bit_size' in child.attributes:
                    bit_size = child.attributes['DW_AT_bit_size'].value
                    bit_offset = child.attributes['DW_AT_bit_offset'].value
                    self.insert_bit_field(field_id, bit_size, bit_offset)
            else:
                # Sometimes there are nested struct/union definitions.
                dies[child.offset] = child
        return symbol_id

    def _tag_pointer_type(self, dies, die_offset, typedef=None):
        """Insert a pointer type."""
        self.debug('_tag_pointer_type 0x{:x}'.format(die_offset))
        die = dies[die_offset - self.cu_offset]
        pointer_size = die.attributes['DW_AT_byte_size'].value
        try:
            pointer_type = die.attributes['DW_AT_type'].value
        except KeyError:
            self.warning('Pointer to void type at DIE 0x{:x}'
                         .format(die_offset))
            pointer_type_id = None
        else:
            pointer_type_id = self._symbol_requires(dies, pointer_type)
            if pointer_type_id is None:
                self.warning('Pointer to unknown type at DIE 0x{:x}.'
                             .format(die_offset))
        # Try to set name to "*pointer_type", otherwise to typedef.
        c = self.database.cursor()
        pointer_name = c.execute('SELECT name FROM symbols WHERE id=?',
                                 (pointer_type_id,)).fetchone()
        c.close()
        if pointer_name is None:
            if not typedef:
                self.debug(
                    'Skipping unnamed pointer type at DIE 0x{:x}'
                        .format(die_offset))
                return None
            else:
                pointer_name = typedef
        else:
            pointer_name = '*' + pointer_name[0]

        symbol_id = self.symbol(pointer_name)
        if symbol_id is not None:
            # Symbol exists
            return symbol_id
        symbol_id = self.insert_symbol(pointer_name, pointer_size)
        self.insert_field(symbol_id, '[pointer]', 0, pointer_type_id,
                          allow_void=True)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_typedef(self, dies, die_offset, typedef=None):
        """Look at what typedef points to and define a symbol with the name of
        the typedef but the properties of what it points to."""
        self.debug('_tag_typedef 0x{:x}'.format(die_offset))
        die = dies[die_offset - self.cu_offset]
        name = die.attributes['DW_AT_name'].value.decode(ElfView.ENCODING)
        try:
            td_offset = die.attributes['DW_AT_type'].value
        except KeyError:
            self.warning('Skipping typedef with no type at DIE 0x{:x}'
                         .format(die_offset))
            return None
        try:
            td_die = dies[td_offset]
        except KeyError:
            raise QuenyaError('Cannot find DIE at offset 0x{:x}'
                              .format(td_offset))
        if isinstance(td_die, int):
            # typedef'd thing already inserted, add reference.
            td_id = td_die
        else:
            # typedef'd thing not inserted. Do that first.
            td_id = self._symbol_requires(dies, td_offset, typedef=name)
            if td_id is None:
                self.warning('Skipping typedef to unknown type at DIE '
                             '0x{:x}'.format(die_offset))
                return None
        # Get name of typedef base type.
        c = self.database.cursor()
        td_name = c.execute('SELECT name FROM symbols WHERE id=?', (td_id,)) \
            .fetchone()[0]
        c.close()
        # If the name is the same, the typedef should fall through to the base
        # type. If the name is different then create a new symbol that refers
        # to the base type.
        if td_name == name:
            symbol_id = td_id
        else:
            symbol_id = self.symbol(name)
            if symbol_id is not None:
                # Symbol exists
                return symbol_id
            if symbol_id is None:
                byte_size = self._die_byte_size(td_id)
                symbol_id = self.insert_symbol(name, byte_size)
            self.insert_field(symbol_id, 'typedef', 0, td_id)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_union_type(self, dies, die_offset, typedef=None):
        """Insert a union."""
        self.debug('_tag_union_type 0x{:x}'.format(die_offset))
        return self._tag_structure_or_union_type(
            dies, die_offset, union=True, typedef=typedef)


def main():
    parser = argparse.ArgumentParser(
        description='Quenya can understand ELF files and create tables or '
                    'output files with symbol and field names.')
    parser.add_argument('-c', '--continue', action='store_true', dest='cont',
                        help='continue adding ELF files if one fails')
    parser.add_argument('--files', nargs='*', default=[],
                        help='elf file(s) to load.')
    parser.add_argument('--database', default=':memory:',
                        help='use an existing database.')
    parser.add_argument('--json', help='JSON output file.')
    parser.add_argument('-q', '--no-log', action='store_true',
                        help='disables all console logging')
    parser.add_argument('--sql', action='store_true',
                        help='stdout the SQL database')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose')
    args = parser.parse_args()

    # Logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(60 if args.no_log else level)
    ch = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Open database
    database = sqlite3.connect(args.database)
    quenya = Quenya(database, logger=logger)

    # Insert ELF files
    loaded = True
    for file in args.files:
        try:
            logger.info('Adding ELF {}'.format(file))
            quenya.insert_elf(file)
        except Exception as e:
            if args.cont:
                logger.exception('Problem adding ELF:')
            else:
                raise e
    if not loaded:
        exit(1)

    # Debug print database
    if args.sql:
        print(quenya.dump)

    database.close()


if __name__ == '__main__':
    main()
