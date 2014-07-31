#!/usr/bin/env python3

import sys

def transform(f, of):
    for line in f:
        line = line.strip().split()
        for part in line:
            part_type, part = part.split('_')
            # WTF? Why we have to have such check at all?
            if part == '': continue

            for letter in part:
                print(letter, part_type, file=of)

        print(file=of)

for filename in sys.argv[1:]:
    with open(filename, 'r') as f: 
        with open(filename + '.conll', 'w') as of:
            transform(f, of)
