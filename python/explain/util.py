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

def get_all_elfs(database):
    """Find all ELF names in database return them."""
    elf_names = database.execute('SELECT name FROM elfs')

    if elf_names is None:
        raise ExplainError('No ELFs imported into database')

    return [name[0] for name in elf_names.fetchall()]
