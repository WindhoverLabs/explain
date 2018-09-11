import argparse
from collections import OrderedDict
import json
from os.path import abspath, dirname
import sqlite3

from explain import explain_elf, explain_symbol
from explain.map import SymbolMap
from explain.elf_reader import ElfReader
from explain.map import ElfMap
from explain.util import get_all_elfs
from explain.serialization import convert

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
    parser.add_argument('--cookiecutter', action='store_true',
                        help='generate serialization cookiecutter json')
    symbol = parser.add_mutually_exclusive_group(required=True)
    symbol.add_argument('-a', '--all', action='store_true',
                        help='output all symbols')
    symbol.add_argument('symbol', nargs='?', help='the symbol name to look at')
    symbol.add_argument('-e', '--everything', action='store_true',
                        help='output all symbols from all files')

    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    if args.database == ':memory:' or args.load:
        elf_reader = ElfReader(db)
        elf_reader.insert_elf(args.file)

    if args.everything:
        if not args.out:
            print('Must specify an out file argument with --out.')
            exit(1)

        out = OrderedDict()
        all_symbols = []
        symbols_dict = {}
        elf_names = get_all_elfs(db)
        for elf_name in elf_names:
            elf = ElfMap.from_name(db, elf_name)
            all_symbols = all_symbols + [explain_symbol(s) for s in elf.symbols()]
            out['little_endian'] = elf['little_endian'] == 1

        for symbol in all_symbols:
            if symbol["name"][0] == '*':
                continue
            symbols_dict[str(symbol["name"])] = symbol
            del symbols_dict[symbol["name"]]["name"]

        sorted_symbols = OrderedDict(sorted(symbols_dict.items()))

        out['files'] = elf_names
        out['cmds'] = {}
        out['tlm'] = {}
        out['symbols'] = sorted_symbols
        with open(args.out, 'w') as fp:
            json.dump(out, fp, indent='    ')
            
        if args.cookiecutter:
            cookie_json = convert(out, dirname(abspath(args.out)))
            
    else:
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
                out = explain_elf(elf, symbols)
                json.dump(out, fp, indent='  ')
                
if __name__ == "__main__":
    main()
