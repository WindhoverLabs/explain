"""
ANSI color printing to terminal.

Functions are named to give them the same length as print.

Adapted from: https://www.geeksforgeeks.org/print-colors-python-terminal/

TODO Find a way to detech color support, and if-def functions to `print` if
    color is disabled.
"""


def prred(txt, *args, **kwargs):
    print("\033[91m {}\033[00m".format(txt), *args, **kwargs)


def prgre(txt, *args, **kwargs):
    print("\033[92m {}\033[00m".format(txt), *args, **kwargs)


def pryel(txt, *args, **kwargs):
    print("\033[93m {}\033[00m".format(txt), *args, **kwargs)


def prblu(txt, *args, **kwargs):
    print("\033[94m {}\033[00m".format(txt), *args, **kwargs)


def prpur(txt, *args, **kwargs):
    print("\033[95m {}\033[00m".format(txt), *args, **kwargs)


def prcya(txt, *args, **kwargs):
    print("\033[96m {}\033[00m".format(txt), *args, **kwargs)


def prbla(txt, *args, **kwargs):
    print("\033[97m {}\033[00m".format(txt), *args, **kwargs)


def prwhi(txt, *args, **kwargs):
    print("\033[98m {}\033[00m".format(txt), *args, **kwargs)


if __name__ == '__main__':
    prred('Red')
    prgre('Green')
    pryel('Yellow')
    prblu('Blue')
    prpur('Purple')
    prcya('Cyan')
    prbla('Black')
    prwhi('White')
