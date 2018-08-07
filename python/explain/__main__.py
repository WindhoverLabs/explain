import argparse
import json
import sqlite3
from collections import OrderedDict

from explain.elf_reader import ElfReader
from explain.map import ElfMap, SymbolMap, FieldMap


def json_symbol(symbol: SymbolMap):
    """Return a dictionary representing the given Symbol with the properties
    needed for this JSON output.

    The important properties for this JSON output are the symbol/field name,
    the bit size, and the bit offset. Typedefs are collapsed and in general
    types are ignored/not useful for the use case of this particular JSON.
    """
    def field(f: FieldMap):
        """Return a dictionary representing the given Field with the properties
        needed for this JSON output.

        This method recurses if the field is a non-simple non-pointer kind.
        """
        fd = OrderedDict()
        fd['name'] = f['name']
        # fd['type'] = f.type.name
        bit_field = f.bit_field
        fd['bit_offset'] = f['byte_offset'] * 8
        if not bit_field:
            fd['bit_size'] = f.type['byte_size'] * 8
        else:
            fd['bit_offset'] += bit_field['bit_offset']
            fd['bit_size'] = bit_field['bit_size']
        kind = f.type
        array = kind.array
        simple = kind.simple
        if array is not None:
            fd['array'] = True
            fd['count'] = array['multiplicity']
            fd['kind'] = json_symbol(array.type.simple)
        elif not simple.is_base_type and not kind.pointer:
            fd['fields'] = [field(f) for f in simple.fields]
        return fd
    sd = OrderedDict()
    sd['name'] = symbol['name']
    sd['bit_size'] = symbol['byte_size'] * 8
    if not symbol.pointer and not symbol.is_primitive:
        sd['fields'] = None if symbol.is_base_type else \
            [field(f) for f in symbol.fields]
    return sd


def json_output(file_stream, elf, symbols):
    """Output a JSON to the file-like stream with the symbols from the ELF.

    Currently there is no name for this kind of JSON because it is the only
    kind of output that Explain has right now. When this changes this output
    will need a real name to differentiate it.
    """
    out = OrderedDict()
    out['file'] = elf['name']
    out['little_endian'] = elf['little_endian'] == 1
    out['symbols'] = [json_symbol(s) for s in symbols]
    json.dump(out, file_stream, indent='  ')


def main():
    parser = argparse.ArgumentParser(
        description='Searches an ElfReader database for a symbol.')
    parser.add_argument('--file', help='ELF file from the database')
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
        elf_reader = ElfReader(db)
        elf_reader.insert_elf(args.file)

    if args.file:
        elf = ElfMap.from_name(db, args.file)
        symbols = (elf.symbol(symbol_name=args.symbol),) if not args.all else \
            elf.symbols()
    else:
        if args.all:
            print('Must specify a file with the -a/--all argument.')
            exit(1)
        symbol = SymbolMap.from_name(db, args.symbol)
        elf = symbol.elf
        symbols = (symbol,)
    if args.print:
        for symbol in symbols:
            symbol.print_tree()

    if args.out:
        with open(args.out, 'w') as fp:
            json_output(fp, elf, symbols)


if __name__ == '__main__':
    main()
