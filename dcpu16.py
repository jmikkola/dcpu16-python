#!/usr/bin/env python2

import sys

def read_label(label):
    ''' parse out a :label '''
    assert(label[0] == ':')
    assert(len(label) > 1)
    return label[1:]

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
    main(sys.argv[1:])
