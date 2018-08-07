# These are the types that struct knows how to unpack.
# Custom types are below.
from explain.explain_error import ExplainError

STRUCT_MAPPING = {
    'char': 'b',
    'unsigned char': 'B',
    'short': 'h',
    'unsigned short': 'H',
    'int': 'i',
    'unsigned int': 'I',
    'long': 'l',
    'unsigned long': 'L',
    'long long': 'q',
    'unsigned long long': 'Q',
    'float': 'f',
    'double': 'd',
    'ptr': 'P'
}
# Custom types that map different type names to common types.
STRUCT_MAPPING['long int'] = STRUCT_MAPPING['long']
STRUCT_MAPPING['long long unsigned int'] = STRUCT_MAPPING['unsigned long long']
STRUCT_MAPPING['long unsigned int'] = STRUCT_MAPPING['unsigned long']
STRUCT_MAPPING['short int'] = STRUCT_MAPPING['short']
STRUCT_MAPPING['short unsigned int'] = STRUCT_MAPPING['unsigned short']
STRUCT_MAPPING['uint64'] = STRUCT_MAPPING['unsigned long']
STRUCT_MAPPING['uint32'] = STRUCT_MAPPING['unsigned int']
STRUCT_MAPPING['uint16'] = STRUCT_MAPPING['unsigned short']
STRUCT_MAPPING['uint8'] = STRUCT_MAPPING['unsigned char']


SYMBOL_FORMAT_MAPPING = {}


def struct_fmt(symbol):
    try:
        return SYMBOL_FORMAT_MAPPING[symbol]
    except KeyError:
        try:
            fmt = STRUCT_MAPPING[symbol['name']]
        except KeyError as e:
            if '*' in symbol['name']:
                bit64 = symbol['byte_size'] == 8
                mapping = 'unsigned long' if bit64 else 'unsigned int'
                fmt = STRUCT_MAPPING[mapping]
            elif symbol['byte_size'] == 4:
                # print('Struct doesn\'t recognize {!r}'.format(symbol.name))
                fmt = STRUCT_MAPPING['unsigned int']
            else:
                raise ExplainError('Can\'t unpack type {!r}'
                                   .format(symbol['name'])) from e
        SYMBOL_FORMAT_MAPPING[symbol] = fmt
        return fmt
