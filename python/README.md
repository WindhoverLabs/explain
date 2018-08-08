# Explain
Explain is a multi-stage Python 3.x library for parsing ELF files and binary data.

Explain contains 3 entry-points for command line use, though more customization
is exposed within Python for future developers to take advantage of.
* Elf Reader
* Explain
* Stream Parser


## Installing via Pip
1. The user should acquire a copy of the explain source distribution, i.e. explain-0.4.tar.gz
2. Using a virtual environment or the default system configuration and Python 
3.5+
   - To create a virtual environment, run `$ virtualenv -p python3.5 venv`
   - To activate run `$ source venv/bin/activate`
   - To deactivate run `$ deactivate`
3. Activate the virtual environment with `$source venv/bin/activate`
4. `pip install <distribution>`


## Elf Reader
`$ elf_reader <database> <file(s)>`

For example, `$ elf_reader cdd.sqllite AMC.so HK.so`

The first point of entry is Elf Reader. Elf Reader produces or updates the 
Sqlite3 database with file name `database` with the DWARF contents from each
file from `files`.

`files` may be a single file or a list of space-separated files to load. Shells
like bash may expand filename wildcards automatically so it is possible to pass
`directory/*.so` to capture every shared-object file in a directory.

## Explain
`$ explain --database database --out output.json symbol`

Explain creates an abstract view of the memory layout for a single symbol (or 
every symbol in an ELF if `--file file` and `--all` are provided). The symbol
layout is saved in a JSON format in the file specified by the `--out` option.

## Stream Parser
`$ parse --database database --csv directory input file_struct`

Stream Parser generates a collection of CSV files representing the decoded
binary log from input. Stream Parser is expecting a CFE/CCSDS-formatted log
file, and takes in an additional structure name that represents the header
for the particular log ('DS_FileHeader_t', etc).

## Building a Distribution
1. Ensure setuptools is installed (use pip)
1. From the Explain (Python) root directory:
2. `python setup.py sdist`
