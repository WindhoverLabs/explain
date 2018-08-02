from explain.symbol import Symbol


def pretty(symbol, indent=0):
    i = '| ' * indent
    for name, value in symbol.items():
        print('{}{} = {!r}'.format(i, name, value))
        if isinstance(value, Symbol):
            pretty(value, indent=indent+1)


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
