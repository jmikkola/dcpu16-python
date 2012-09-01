#!/usr/bin/env python2

import sys
import re
import collections

Value = collections.namedtuple('Value', ['kind', 'indirect', 'value'])

class ParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def read_label(token):
    ''' parse out a :label '''
    assert(token)
    if len(token) <= 1 or token[0] != ':':
        raise ParseError('Label must be of format :label, not ' + token)
    return token[1:]

literalRe = re.compile(r'0x[0-9a-fA-F]{1,4}')
def read_value(token):
    ''' parse a value '''
    assert(token)
    if len(token) == 1 and token in 'ABCXYZIJ':
        return Value('Register', False, token)
    elif token in {'POP', 'PEEK', 'PUSH'}:
        return Value('Command', False, token)
    elif literalRe.match(token):
        return Value('Literal', False, int(token, 16))
    elif token[0] == '[' and token[-1] == ']':
        inner = token[1:-1]
        if len(inner) == 1 and inner in 'ABCXYZIJ':
            return Value('Register', True, inner)
        elif literalRe.match(inner):
            return Value('Literal', True, int(inner, 16))
    raise ParseError('Expected a value, found ' + token)

def read_instruction(line):
    return None

def parse_line(line):
    parts = line.strip().split()
    if parts and parts[0][0] == ':':
        yield read_label(parts[0])
        parts = parts[1:]
    for part in parts:
        if part[0] == ';':
            break
        yield part

def parse(inf):
    ''' A simple line-based parser '''
    for line in inf:
        for item in parse_line(line):
            yield item

def main(args):
    if args:
        fname = args[0]
        with open(fname, 'r') as inf:
            for x in parse(inf):
                print x
    else:
        for x in parse(sys.stdin):
            print x

if __name__ == '__main__':
    pass
    #main(sys.argv[1:])
