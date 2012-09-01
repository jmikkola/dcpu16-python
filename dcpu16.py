#!/usr/bin/env python2

import sys
import re

class ParseItem:
    def is_value():
        return False
    def is_instruction():
        return False
    def is_label():
        return False
    def output(labels):
        return []

class Value(ParseItem):
    def __init__(self, kind, indirect, value, plus=None):
        self.kind = kind
        self.value = value
        self.indirect = indirect
        self.plus = plus
    def is_value():
        return True
    def __str__(self):
        s = ['['] if self.indirect else []
        s.append(str(self.value))
        if self.plus: s.extend(['+', self.plus])
        if self.indirect: s.append(']')
        return ''.join(s)
    def __repr__(self):
        return "Value(%s, %s, %s, %s)" % (
            repr(self.kind), repr(self.indirect), repr(self.value), repr(self.plus))

class Label(ParseItem):
    def __init__(self, label):
        self.label = label
    def is_label():
        return True
    def __str__(self):
        return ':' + self.label
    def __repr__(self):
        return 'Label(%s)' % repr(self.label)

class Instruction(ParseItem):
    def __init__(self, opcode, num_values):
        self.opcode = opcode
        self.num_values = num_values
    def is_instruction():
        return True
    def __str__(self):
        return self.opcode
    def __repr__(self):
        return 'Instruction(%s, %d)' % (repr(self.opcode), self.num_values)

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
    return Label(token[1:])

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
        return Value('Command', indirect, token)
    if len(token) == 1 and token in registers:
        return Value('Register', indirect, token)

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

def assemble(items):
    for x in items:
        print x

def main(args):
    if args:
        fname = args[0]
        with open(fname, 'r') as inf:
            assemble(parse(inf))
    else:
        assemble(parse(sys.stdin))

if __name__ == '__main__':
    main(sys.argv[1:])
    #pass
