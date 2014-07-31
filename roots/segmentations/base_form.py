
import re
import operator


from rwe.exception import ExtractException

import rwe.segmentations.yot as yot

def calc_part_order_and_name(part):
    """
    Вычисляет порядок и окончательный тег морфемы.

    Calculate order and final tag of morpheme.
    """
    if part[:len('префд')] == 'префд':
        return int(part[len('префд'):]), 'префд'
    elif re.match('прист?[1-3]$', part):
        return 10 + int(part[-1:]), 'прист'
    elif part == 'прист':
        return 10, 'прист'
    elif re.match('корень?1?$', part):
        return 20, 'корень'
    elif re.match('суфф-[1-4]$', part):
        return 30 + int(part[5]), 'суфф'
    elif part == 'оконч-1':
        return 40, 'оконч'
    elif re.match('соед1?$', part):
        return 50, 'соед'
    elif re.match('прист2[1-2]$', part):
        return 60 + int(part[6]), 'прист'
    elif part == 'корень2':
        return 70, 'корень'
    elif re.match('суфф-2[1-4]$', part):
        return 80 + int(part[6]), 'суфф'
    elif part == 'соед2':
        return 90, 'соед'
    elif re.match('прист3[1-2]$', part):
        return 100 + int(part[6]), 'прист'
    elif part == 'корень3':
        return 110, 'корень'
    elif part == 'интер':
        return 120, 'интер'
    elif part == 'суффд1':
        return 130, 'суффд'
    elif re.match('суфф?[1-5]$', part):
        return 140 + int(part[-1:]), 'суфф'
    elif part == 'суфф':
        return 140, 'суфф'
    elif part[:len('оконч')] == 'оконч':
        return 150, 'оконч'
    elif part == 'частица'[:len(part)] or part == 'постфикс':
        return 160, 'частица'
    else:
        raise Exception(part)



"""
Список частей слов, которые были оперделены едиными морфемами где-то
на просторах русского викисловаря. Список, разумеется, не исчерпывающий.

Word parts which were incorrectly identified as single morphemes.
List is not exhausting, of course.
"""
error_parts = set(['ибелен', 'распре', 'ёхонек', 'ителен', 'надцат', 'привет', 'исмент', 'абелен', 'глобус', 'ирован'])


"""
Порядок морфем в шаблоне {{{морфо}}}, когда аргументы шаблона не
определены явно.

Order of morphemes in {{{морфо}}} template, when template's arguments 
are not named.
"""
morphemes_order = ['прист1', 'корень1', 'суфф1', 'оконч', 'частица']


def extract_base_form_segmentation(morfo):
    """
    Извлекает разбиение на морфемы начальной формы слова из шаблона {{{морфо}}}.

    Extracts segmentation from {{{морфо}}} template.
    """
    segmented = morfo[2:-2].split('|')[1:]

    normalized = []
    i = 0
    for part in segmented:
        if part == '':
            i += 1
            continue

        split_index = part.find('=')
        if split_index == len(part) - 1:
            continue

        part_order = None
        part_name = None
        if split_index > -1:
            part_name_match = re.match('[^=]+', part)
            part_name = part_name_match.group(0)
            if part_name == 'источник':
                continue
            if part_name == 'постфикс':
                part_name = 'частица'
            part_order, part_name = calc_part_order_and_name(part_name)
            part = part[split_index + 1:].replace('ь', '').replace('ъ', '')
        elif i < len(morphemes_order):
            part_order, part_name = calc_part_order_and_name(morphemes_order[i])
            part = part.replace('ь', '').replace('ъ', '')
            i += 1
        else:
            raise ExtractException(i, part, morfo)

        if part_name != 'корень' and (len(part) > 6 or part in error_parts):
            raise ExtractException(i, part_name, part)
        normalized.append((part_order, part_name, part))

    sorted_and_normalized = list(map(lambda t: t[1:], sorted(normalized, key=operator.itemgetter(0))))
    return yot.replace_yot(sorted_and_normalized)

def check_for_root_presence(segmentation):
    return any(map(lambda s: s[0] == 'корень', segmentation))
