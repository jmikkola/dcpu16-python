#!/usr/bin/env python2

import sys
import re

class ParseItem:
    def is_instruction(self):
        return False

    def is_label(self):
        return False

class Label(ParseItem):
    def __init__(self, label):
        self.label = label

    def is_label(self):
        return True

    @classmethod
    def parse(cls, token):
        ''' parse out a :label '''
        assert(token)
        if len(token) <= 1 or token[0] != ':':
            raise ParseError('Label must be of format :label, not ' + token)
        return cls(token[1:])

    def __str__(self):
        return ':' + self.label

    def __repr__(self):
        return 'Label(%s)' % repr(self.label)

class Value:
    commands = {
        'POP':  0x18, 'PEEK': 0x19, 'PUSH': 0x1A,
        'SP':   0x1B, 'PC':   0x1C, 'O':    0x1D
    }
    registers = {
        'A': 0, 'B': 1, 'C': 2,
        'X': 3, 'Y': 4, 'Z': 5,
        'I': 6, 'J': 7
    }
    literalRe = re.compile(r'^\d+$')
    literalRe16 = re.compile(r'^0x[0-9a-fA-F]{1,4}$')
    labelRe = re.compile(r'^\w+$')

    @classmethod
    def parse(cls, token):
        assert(token)

        # Is access indirect?
        indirect = False
        if token[0] == '[' and token[-1] == ']':
            token = token[1:-1]
            indirect = True

        # Values that cannot have a register offset
        if token in cls.commands:
            return cls(cls.commands[token], indirect)
        if len(token) == 1 and token in cls.registers:
            r = cls.registers[token]
            if indirect: r += 8
            return cls(r, indirect)

        # Does it have a register offset?
        offset = None
        if indirect and (len(token) > 1 and token[-2] == '+'):
            offset = token[-1]
            if offset not in cls.registers:
                raise ParseError('Bad register offset: ' + offset)
            r = cls.registers[offset]
            token = token[:-2]

        # Values that can have a register offset
        if cls.literalRe.match(token):
            literal = int(token)
            if not indirect and 0 <= literal < 0x20:
                return cls(literal + 0x20)
            if offset:
                value = 0x10 + r
            elif indirect:
                value = 0x1e
            else:
                value = 0x1f
            return cls(value, hasNextWord=True, nextWord=literal)
        if cls.literalRe16.match(token):
            literal = int(token, 16)
            if not indirect and 0 <= literal < 0x20:
                return cls(literal + 0x20)
            if offset:
                value = 0x10 + r
            elif indirect:
                value = 0x1e
            else:
                value = 0x1f
            return cls(value, hasNextWord=True, nextWord=literal)
            return cls('Literal', indirect, int(token, 16), plus)
        if cls.labelRe.match(token):
            value = 0x1e if indirect else 0x1f
            return cls(value, hasNextWord=True, label=token)
        raise ParseError('Expected a value, found ' + token)


    def __init__(self, value, hasNextWord=False, nextWord=None, label=None):
        self.value = value
        self.nextWord = nextWord if nextWord else 0
        self.hasNextWord = hasNextWord
        self.label = label

    def __str__(self):
        # TODO: un-parse value
        return repr(self)

    def __repr__(self):
        return "Value(%s, %s)" % (repr(self.value), repr(self.nextValue))

    def requires_lookup(self):
        return self.hasNextWord and self.label is not None

class Instruction(ParseItem):
    values = {
        'SET': 0x01, 'ADD': 0x02, 'SUB': 0x03, 'MUL': 0x04, 'DIV': 0x05, 'MOD': 0x06,
        'SHL': 0x07, 'SHR': 0x08, 'AND': 0x09, 'BOR': 0x0A, 'XOR': 0x0B, 'IFE': 0x0C,
        'IFN': 0x0D, 'IFG': 0x0E, 'IFB': 0x0F, 'JSR': 0x10
        }

    @classmethod
    def parse(cls, tokens):
        if not (2 <= len(tokens) <= 3):
            raise ParseError('Expected 2 or 3 part instruction: ' + str(tokens))

        opcode = tokens[0]
        if opcode not in cls.values:
            raise ParseError('Invalid opcode: ' + opcode)
        instruction = cls(cls.values[opcode])

        values = tokens[1:]
        if len(values) != instruction.num_values():
            raise ParseError('Wrong number of values for ' + str(instruction))
        if len(values) == 1:
            instruction.values.append(Value.parse(values[0]))
        else:
            # TODO: check for comma
            instruction.values.append(Value.parse(values[0][:-1]))
            instruction.values.append(Value.parse(values[1]))
        return instruction

    def __init__(self, opcode):
        self.opcode = opcode
        self.values = []

    def is_instruction(self):
        return True

    def num_values(self):
        return 2 if (self.opcode != 0x10) else 1

    def __str__(self):
        return self.opcode

    def __repr__(self):
        return 'Instruction(%s, %d)' % (repr(self.opcode), self.num_values)

    def output(self):
        # Output instruction's word
        instruction = self.opcode
        for v in self.values:
            pass
        # TODO: insert values into instruction
        yield (instruction, None)
        # Output next words
        for v in self.values:
            if v.hasNextWord:
                yield (v.nextWord, v.label)

class ParseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def strip_comment(line):
    index = line.find(';')
    return line[:index] if index >= 0 else line

def parse_line(line):
    tokens = strip_comment(line).strip().split()
    while tokens and tokens[0][0] == ':':
        yield Label.parse(tokens[0])
        tokens = tokens[1:]
    # TODO: allow parsing a hex literal
    if tokens:
        yield Instruction.parse(tokens)

def parse(inf):
    ''' A simple line-based parser '''
    for line in inf:
        for item in parse_line(line):
            yield item

def assemble(items):
    data = []
    labels = {}
    updateLocations = {}

    wordPosition = 0
    for x in items:
        if x.is_instruction():
            for (value, label) in x.output():
                data.append(value)
                if label:
                    updateLocations[len(data) - 1] = label
        else:
            label = x.label
            if label in labels:
                raise ParseError("duplicate label: " + label)
            labels[label] = len(data)

    for location, label in updateLocations.iteritems():
        if label not in labels:
            raise ParseError("could not find label: " + label)
        labelLocation = labels[label]
        data[location] = labelLocation
    return data

def run(inf):
    data = assemble(parse(inf))
    for word in data:
        print('%x' % word)


def main(args):
    if args:
        fname = args[0]
        with open(fname, 'r') as inf:
            run(inf)
    else:
        run(sys.stdin)

if __name__ == '__main__':
    main(sys.argv[1:])
