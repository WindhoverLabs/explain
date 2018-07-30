"""
ANSI color printing to terminal.

Functions are named to give them the same length as print.

Adapted from: https://www.geeksforgeeks.org/print-colors-python-terminal/

TODO Find a way to detect color support, and if-def functions to `print` if
    color is disabled.
"""


def prred(txt, *args, **kwargs):
    print("\033[91m {}\033[00m".format(txt), *args, **kwargs)


def pgree(txt, *args, **kwargs):
    print("\033[92m {}\033[00m".format(txt), *args, **kwargs)


def pyell(txt, *args, **kwargs):
    print("\033[93m {}\033[00m".format(txt), *args, **kwargs)


def pblue(txt, *args, **kwargs):
    print("\033[94m {}\033[00m".format(txt), *args, **kwargs)


def ppurp(txt, *args, **kwargs):
    print("\033[95m {}\033[00m".format(txt), *args, **kwargs)


def pcyan(txt, *args, **kwargs):
    print("\033[96m {}\033[00m".format(txt), *args, **kwargs)


def pblac(txt, *args, **kwargs):
    print("\033[97m {}\033[00m".format(txt), *args, **kwargs)


def pwhit(txt, *args, **kwargs):
    print("\033[98m {}\033[00m".format(txt), *args, **kwargs)


if __name__ == '__main__':
    prred('Red')
    pgree('Green')
    pyell('Yellow')
    pblue('Blue')
    ppurp('Purple')
    pcyan('Cyan')
    pblac('Black')
    pwhit('White')
