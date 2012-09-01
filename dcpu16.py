#!/usr/bin/env python2

import sys
import re
import collections

Value = collections.namedtuple('Value', ['kind', 'indirect', 'value', 'plus'])
Instruction = collections.namedtuple('Instruction', ['opcode', 'num_values'])

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

literalRe = re.compile(r'^\d+$')
literalRe16 = re.compile(r'^0x[0-9a-fA-F]{1,4}$')
labelRe = re.compile(r'^\w+$')
commands = {'POP', 'PEEK', 'PUSH', 'SP', 'PC', 'O'}
registers = 'ABCXYZIJ'
def read_value(token):
    ''' parse a value '''
    assert(token)

    # Is access indirect?
    indirect = False
    if token[0] == '[' and token[-1] == ']':
        token = token[1:-1]
        indirect = True

    # Values that cannot have a register offset
    if token in commands:
        return Value('Command', indirect, token, None)
    if len(token) == 1 and token in registers:
        return Value('Register', indirect, token, None)

    # Does it have a register offset?
    plus = None
    if indirect and (len(token) > 1 and token[-2] == '+'):
        plus = token[-1]
        if plus not in registers:
            raise ParseError('Bad register offset: ' + plus)
        token = token[:-2]

    # Values that can have a register offset
    if literalRe.match(token):
        return Value('Literal', indirect, int(token), plus)
    if literalRe16.match(token):
        return Value('Literal', indirect, int(token, 16), plus)
    if labelRe.match(token):
        return Value('label', indirect, token, plus)
    raise ParseError('Expected a value, found ' + token)

def strip_comment(line):
    index = line.find(';')
    return line[:index] if index >= 0 else line

basicOpcodes = set('SET ADD SUB MUL DIV MOD SHL SHR AND BOR XOR IFE IFN IFG IFB'.split())
def read_instruction(token):
    assert(token)
    if token == 'JSR':
        return Instruction(token, 1)
    elif token in basicOpcodes:
        return Instruction(token, 2)
    else:
        raise ParseError('Bad opcode ' + token);

def parse_line(line):
    tokens = strip_comment(line).strip().split()
    state = 1
    for token in tokens:
        if state == 1 and token[0] == ':':
            state = 2
            yield read_label(token)
        elif state in [1,2]:
            instruction = read_instruction(token)
            state = 5 - instruction.num_values
            yield instruction
        elif state in [3,4]:
            if state == 3:
                if token[-1] == ',': token = token[:-1]
                else: raise ParseError("Expected value to end with a ',': " + token)
            state += 1
            yield read_value(token)
        else:
            raise ParseError('Did not expect %s in state %d' % (token, state))
    if state not in [1,2,5]:
        raise ParseError('Line ended before parse finished. Final state: %d' % state)

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
    main(sys.argv[1:])
