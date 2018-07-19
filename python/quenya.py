import argparse
import hashlib
import os
import sqlite3

from elftools.elf.elffile import ELFFile

from ansi_color import *


def get_or_zero(die, name):
    try:
        return die.attributes.get(name).value
    except AttributeError:
        return 0


def recur_children(die, indent=''):
    path = die.get_full_path()
    # path = get_none(die, 'DW_AT_name')
    type = get_or_zero(die, 'DW_AT_type')
    byte_offset = get_or_zero(die, 'DW_AT_data_member_location')
    byte_size = get_or_zero(die, 'DW_AT_byte_size')
    bit_size = get_or_zero(die, 'DW_AT_bit_size')
    bit_offset = get_or_zero(die, 'DW_AT_bit_offset')
    # struct_type = get_or_zero(die, 'DW_TAG_structure_type')

    # print(die.attributes.keys())

    bit_size = bit_size + (byte_size * 8)
    bit_offset = bit_offset + (byte_offset * 8)

    print('{}{!s:<{pad}} | {!s:>6} | {!s:>6} | {!s:>6}'.format(
        indent, path, type, bit_size, bit_offset, pad=40-len(indent)
    ))

    for child in die.iter_children():
        recur_children(child, indent + '..')


class QuenyaError(Exception):
    """Base type for Quenya Errors."""


class Quenya(object):
    """Quenya, the language of the High Elves"""
    def __init__(self, db_file):
        self.database = sqlite3.connect(db_file)
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
        c.execute('CREATE TABLE IF NOT EXISTS elfs ('
                  'id INTEGER PRIMARY KEY,'
                  'name TEXT NOT NULL,'
                  'checksum TEXT NOT NULL,'
                  'date DATETIME NOT NULL DEFAULT(CURRENT_TIMESTAMP),'
                  'little_endian BOOLEAN NOT NULL,'
                  'UNIQUE (name, checksum)'
                  ')')
        c.execute('CREATE TABLE IF NOT EXISTS symbols ('
                  'id INTEGER PRIMARY KEY,'
                  'elf INTEGER NOT NULL,'
                  'name TEXT NOT NULL,'
                  'size INTEGER NOT NULL,'
                  'FOREIGN KEY(elf) REFERENCES elfs(id),'
                  'UNIQUE (name, elf)'
                  ')')
        c.execute('CREATE TABLE IF NOT EXISTS fields('
                  'id INTEGER PRIMARY KEY,'
                  'symbol INTEGER NOT NULL,'
                  'bit_offset INTEGER NOT NULL,'
                  'name TEXT NOT NULL,'
                  'type INTEGER NOT NULL,'
                  'multiplicity INTEGER NOT NULL,'
                  'FOREIGN KEY (symbol) REFERENCES symbols(id),'
                  'FOREIGN KEY (type) REFERENCES symbols(id)'
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
                      (file_name, sqlite3.Binary(checksum), elf.little_endian))
        except sqlite3.IntegrityError:
            c.execute('SELECT date FROM elfs WHERE checksum=? AND name=?',
                      (checksum, base))
            duplicate = c.fetchone()
            raise QuenyaError('{!r} matched previously loaded ELF uploaded on '
                              '{}'.format(base, duplicate[0]))

        # Insert symbols from ELF
        elf_id = c.lastrowid
        self.insert_symbols(elf, elf_id)
        return True

    def insert_symbols(self, elf, elf_id):
        # print(elf.header)
        dwarf = elf.get_dwarf_info()
        for i, cu in enumerate(dwarf.iter_CUs()):
            print('CU #{}: {}'.format(i, cu.header))
            top = cu.get_top_DIE()
            print(top)
            for child in top.iter_children():
                print(child)
        #     recur_children(cu.get_top_DIE(), '')
        #
        #     print(die)
        #     print(die.get_full_path())


def main():
    parser = argparse.ArgumentParser(
        description='Elvish can understand ELF files and create tables or '
                    'output files with symbol and field names.')
    parser.add_argument('--files', nargs='*', default=[],
                        help='elf file(s) to load.')
    parser.add_argument('--database', default=':memory:',
                        help='use an existing database.')
    parser.add_argument('--json', help='JSON output file.')
    args = parser.parse_args()

    # Open database
    elvish = Quenya(args.database)

    # Load required files
    loaded = True
    for file in args.files:
        try:
            elvish.insert_elf(file)
        except QuenyaError as e:
            prred(e)
            loaded = False
    if not loaded:
        exit(1)

    # Debug print database
    # print('\n\n')
    # for line in elvish.database.iterdump():
    #     print(line)


if __name__ == '__main__':
    main()
