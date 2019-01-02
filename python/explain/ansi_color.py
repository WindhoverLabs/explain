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
