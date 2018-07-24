"""
Code Limitations:
    ELF files to be parsed must conform to the following requirements:
    1. All relevant typedefs, structs, and unions must be defined in the top-
        level of a file. Quenya will not look inside function definitions.
    2. Structs and unions which are typedef'd must have either the same tag as
        their typedef or be untagged.
"""

import argparse
import hashlib
import logging
import os
import sqlite3

from elftools.elf.elffile import ELFFile

from ansi_color import *


class QuenyaError(Exception):
    """Base type for Quenya Errors."""


class Quenya(object):
    """Quenya, the language of the High Elves"""

    def __init__(self, db_file, logger=None):
        self.database = sqlite3.connect(db_file)
        self.logger = logger
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
        # Note: sqlite does not store binary data. Must use sqlite.Binary
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
            'bit_offset INTEGER NOT NULL,'
            'type INTEGER,'
            'multiplicity INTEGER NOT NULL,'
            'FOREIGN KEY (symbol) REFERENCES symbols(id),'
            'FOREIGN KEY (type) REFERENCES symbols(id),'
            'UNIQUE (symbol, name)'
            ')')
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
        elf_view.insert_symbols(elf)
        return True


class ElfView(object):
    ENCODING = 'utf-8'

    def __init__(self, database, elf_id, logger=None):
        self.database = database
        self.elf_id = elf_id
        self.logger = logger

    def insert_enumeration(self, symbol_id, value, name):
        self.logger.debug('insert_enumeration {} {} {}'.format(
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

    def insert_field(self, symbol_id, name, bit_offset, kind, multiplicity=0,
                     allow_void=False):
        if kind is None and not allow_void:
            raise QuenyaError('Attempted to add a void field type without '
                              'explicit override.')
        self.logger.debug('insert_field {} {} {} {}'.format(
            symbol_id, name, bit_offset, kind, multiplicity))
        c = self.database.cursor()
        field_id = c.execute('SELECT id FROM fields WHERE symbol=? AND name=?',
                             (symbol_id, name)).fetchone()
        if field_id is None:
            c.execute('INSERT INTO fields(symbol, name, bit_offset, type,'
                      'multiplicity) VALUES (?, ?, ?, ?, ?)',
                      (symbol_id, name, bit_offset, kind, multiplicity))
            field_id = c.lastrowid
        else:
            field_id = field_id[0]
        c.close()
        return field_id

    def insert_symbol(self, name, byte_size):
        """Insert a symbol with name and byte_size."""
        self.logger.debug('insert_symbol {} (size={})'.format(name, byte_size))
        c = self.database.cursor()
        symbol_id = c.execute('SELECT id FROM symbols WHERE elf=? AND '
                              'name=?', (self.elf_id, name)).fetchone()
        if symbol_id is None:
            c.execute('INSERT INTO symbols(elf, name, byte_size)'
                      'VALUES(?, ?, ?)', (self.elf_id, name, byte_size))
            symbol_id = c.lastrowid
        else:
            symbol_id = symbol_id[0]
        c.close()
        return symbol_id

    def insert_symbols(self, elf):
        # print(elf.header)
        dwarf = elf.get_dwarf_info()

        for i, cu in enumerate(dwarf.iter_CUs()):
            self.logger.debug('CU #{}: {}'.format(i, cu.header))
            top = cu.get_top_DIE()
            dies = {c.offset - cu.cu_offset: c for c in top.iter_children()}
            self.cu_offset = cu.cu_offset

            for child in top.iter_children():
                self._symbol_requires(dies, child.offset - self.cu_offset)

    def _symbol_requires(self, dies, offset, typedef=None):
        self.logger.debug('_symbol_requires {} (typedef={!r})'.format(
            hex(offset), typedef))
        # print(die_dict)
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
            'DW_TAG_reference_type': self._tag_skip,
            'DW_TAG_subprogram': self._tag_skip,
            'DW_TAG_subroutine_type': self._tag_skip,
            'DW_TAG_variable': self._tag_skip,
        }
        symbol = dies[offset]
        if isinstance(symbol, int):
            self.logger.debug('Found inserted symbol id = {}'.format(symbol))
            return symbol
        try:
            callback = known_tags[symbol.tag]
        except KeyError as e:
            raise QuenyaError('symbol_requires can\'t handle\n' + str(symbol)) \
                from e
        return callback(dies, symbol.offset, typedef=typedef)

    def _die_byte_size(self, die_offset):
        """Get the byte size of a DIE."""
        self.logger.debug('_die_byte_size {}'.format(str(die_offset)[:20]))
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
                raise QuenyaError('Can\'t get size of {} at DIE {}'.format(
                    tag, hex(die_offset)))
        return size

    def _tag_array_type(self, dies, die_offset, typedef=None):
        self.logger.debug('_tag_array_type {}'.format(hex(die_offset)))
        die = dies[die_offset - self.cu_offset]
        array_type = die.attributes['DW_AT_type'].value
        array_type_id = self._symbol_requires(dies, array_type)
        c = self.database.cursor()
        c.execute('SELECT name, byte_size FROM symbols WHERE id=?',
                  (array_type_id,))
        array_type_name, unit_byte_size = c.fetchone()
        c.close()
        multiplicity = -1
        for child in die.iter_children():
            if multiplicity != -1:
                raise QuenyaError('Multiple array children at:\n' + str(die))
            if child.tag == 'DW_TAG_subrange_type':
                multiplicity = child.attributes['DW_AT_upper_bound'].value + 1
            else:
                raise QuenyaError('Unknown array child at:\n' + str(die))
        array_name = 'array_{}_{}'.format(array_type_name, multiplicity)
        symbol_size = unit_byte_size * multiplicity
        symbol_id = self.insert_symbol(array_name, symbol_size)
        self.insert_field(symbol_id, '[array]', 0, array_type_id, multiplicity)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_base_type(self, dies, die_offset, typedef=None):
        self.logger.debug('_tag_base_type {}'.format(hex(die_offset)))
        die = dies[die_offset - self.cu_offset]
        name = die.attributes['DW_AT_name'].value.decode(ElfView.ENCODING)
        size = die.attributes['DW_AT_byte_size'].value
        symbol_id = self.insert_symbol(name, size)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_enumeration_type(self, dies, die_offset, typedef=None):
        self.logger.debug('_tag_enumeration_type {}'.format(hex(die_offset)))
        die = dies[die_offset - self.cu_offset]
        if not typedef:
            self.logger.debug('Skipping direct enum at {}'.format(
                hex(die_offset)))
            return
        symbol_name = typedef
        symbol_byte_size = die.attributes['DW_AT_byte_size'].value
        symbol_id = self.insert_symbol(symbol_name, symbol_byte_size)
        for child in die.iter_children():
            cname = child.attributes['DW_AT_name']\
                .value.decode(ElfView.ENCODING)
            cvalue = child.attributes['DW_AT_const_value'].value
            self.insert_enumeration(symbol_id, cvalue, cname)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_skip(self, dies, die_offset, typedef=None):
        self.logger.debug('Skipping known tag {} at {} (typedef={!r})'.format(
            dies[die_offset - self.cu_offset].tag, hex(die_offset), typedef))

    def _tag_structure_type(self, dies, die_offset, typedef=None):
        self.logger.debug('_tag_structure_type {}'.format(hex(die_offset)))
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
                self.logger.debug('Skipping unnamed {} at {}'.format(
                    kind, hex(die_offset)))
                return
            symbol_name = typedef
        byte_size = die.attributes['DW_AT_byte_size'].value
        symbol_id = self.insert_symbol(symbol_name, byte_size)
        for child in die.iter_children():
            field_name = child.attributes['DW_AT_name'] \
                .value.decode(ElfView.ENCODING)
            self.logger.debug(kind + ' ' + symbol_name + '.' + field_name)
            # TODO make it work with bit fields!
            if 'DW_AT_bit_size' in child.attributes:
                raise QuenyaError(kind + ' contains bit-fields at DIE ' +
                                  hex(die_offset))
            byte_offset = 0 if union else \
                child.attributes['DW_AT_data_member_location'].value
            bit_offset = byte_offset * 8
            field_type = child.attributes['DW_AT_type'].value
            field_type_id = self._symbol_requires(
                dies, field_type, typedef=field_name)
            if field_type_id is None:
                raise QuenyaError('Field {} has no type at DIE {}'
                                  .format(field_name, hex(die_offset)))
            self.insert_field(symbol_id, field_name, bit_offset, field_type_id)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_pointer_type(self, dies, die_offset, typedef=None):
        self.logger.debug('_tag_pointer_type {}'.format(hex(die_offset)))
        die = dies[die_offset - self.cu_offset]
        if not typedef:
            self.logger.debug('Skipping unnamed pointer type at DIE {}'.format(
                hex(die_offset)))
            return
        pointer_name = typedef
        pointer_size = die.attributes['DW_AT_byte_size'].value
        pointer_type = die.attributes['DW_AT_type'].value
        pointer_type_id = self._symbol_requires(dies, pointer_type)
        if pointer_type_id is None:
            self.logger.warning('Pointer to unknown or void type at DIE {}.'
                                .format(hex(die_offset)))
        symbol_id = self.insert_symbol(pointer_name, pointer_size)
        self.insert_field(symbol_id, '[pointer]', 0, pointer_type_id,
                          allow_void=True)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_typedef(self, dies, die_offset, typedef=None):
        """Look at what typedef points to and define a symbol with the name of
        the typedef but the properties of what it points to."""
        self.logger.debug('_tag_typedef {}'.format(hex(die_offset)))
        die = dies[die_offset - self.cu_offset]
        name = die.attributes['DW_AT_name'].value.decode(ElfView.ENCODING)
        td_offset = die.attributes['DW_AT_type'].value
        try:
            td_die = dies[td_offset]
        except KeyError:
            raise QuenyaError('Cannot find DIE at offset ' + hex(td_offset))
        if isinstance(td_die, int):
            # typedef'd thing already inserted, add reference.
            td_id = td_die
        else:
            # typedef'd thing not inserted. Do that first.
            td_id = self._symbol_requires(dies, td_offset, typedef=name)
            if td_id is None:
                self.logger.debug('Skipping typedef to unknown type at DIE {}'
                                  .format(hex(die_offset)))
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
            byte_size = self._die_byte_size(td_id)
            symbol_id = self.insert_symbol(name, byte_size)
            self.insert_field(symbol_id, 'typedef', 0, td_id)
        dies[die_offset - self.cu_offset] = symbol_id
        return symbol_id

    def _tag_union_type(self, dies, die_offset, typedef=None):
        self.logger.debug('_tag_union_type {}'.format(hex(die_offset)))
        return self._tag_structure_or_union_type(
            dies, die_offset, union=True, typedef=typedef)


def main():
    parser = argparse.ArgumentParser(
        description='Quenya can understand ELF files and create tables or '
                    'output files with symbol and field names.')
    parser.add_argument('--files', nargs='*', default=[],
                        help='elf file(s) to load.')
    parser.add_argument('--database', default=':memory:',
                        help='use an existing database.')
    parser.add_argument('--json', help='JSON output file.')
    parser.add_argument('--sql', action='store_true',
                        help='stdout the SQL database')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose')
    args = parser.parse_args()

    # Logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(logging.StreamHandler())

    # Open database
    elvish = Quenya(args.database, logger=logger)

    # Insert ELF files
    loaded = True
    for file in args.files:
        try:
            logger.info('Adding ELF {}'.format(file))
            elvish.insert_elf(file)
        except QuenyaError as e:
            prred(e)
            loaded = False
    if not loaded:
        exit(1)

    # Debug print database
    if args.sql:
        for line in elvish.database.iterdump():
            print(line)


if __name__ == '__main__':
    main()
