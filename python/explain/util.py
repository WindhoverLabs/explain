from explain.symbol import Symbol, ArraySymbol


def pretty(symbol, indent=0):
    i = '| ' * indent
    for name, value in symbol.items():
        print('{}{} = {!r}'.format(i, name, value))
        if isinstance(value, Symbol):
            pretty(value, indent=indent+1)


def flatten(symbol, name='', join_chr=True):
    name = name or symbol.symbol.name
    if isinstance(symbol, ArraySymbol):
        if join_chr and 'char' in symbol.symbol.name:
            print('{} = char {!r}'.format(name, ''.join(chr(c.value) for c in symbol)))
        else:
            for n, elem in enumerate(symbol):
                flatten(elem, name + '[{}]'.format(n), join_chr)
    else:
        print('{} = {}'.format(name, symbol.value))
        if isinstance(symbol, Symbol):
            for n, elem in symbol.items():
                flatten(elem, name + '.' + n, join_chr)


def sql_print(result, header_every=20):
    """Utility method to pretty-print the result of a SQLite Query.

    Usage:
        >>> import sqlite3
        >>> result = sqlite3.connect().execute("sql query")
        >>> sql_print(result)
    """
    header = [d[0] for d in result.description]
    rows = [[str(c) for c in r] for r in result]
    rows_len = [[len(c) for c in r] for r in rows]

    col_widths = list(map(max, zip((len(h) for h in header), *rows_len)))

    def format_row(row, header=False):
        fmt = ' | '.join('{{:>{w}}}'.format(w=cw) for cw in col_widths)
        fmtd = fmt.format(*row)
        if header:
            print('#' * len(fmtd))
        print(fmtd)

    i = 0
    for row in rows:
        if (header_every is None and i == 0) \
                or (isinstance(header_every, int) and not i % header_every):
            format_row(header, header=True)
        format_row(row)
        i += 1
