#!/usr/bin/env python3

# Конвертурует вывод данной программы в типичный CoNLL 
# формат с двумя столбцами - буквой и частью слова

# Converts segmentations from main programm format to
# standart CoNLL with two columns - letter and part type

import sys

def transform(f, of):
    for line in f:
        line = line.strip().split()
        for part in line:
            part_type, part = part.split('_')
            # Why we have to have such check at all?
            if part == '': continue

            print(part[0], ' ', part_type, '_начало', sep='', file=of)
            for letter in part[1:]:
                print(letter, part_type, file=of)

        print(file=of)

for filename in sys.argv[1:]:
    with open(filename, 'r') as f: 
        with open(filename + '.conll', 'w') as of:
            transform(f, of)
