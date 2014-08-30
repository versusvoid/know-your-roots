"""
Загрузка и обработка ранее сохранённых шаблонов таблиц склонения и спряжения.

Loading and processing of plain text declension and conjugation tables' templates.
"""

import os
import re
import sys

import logging
logger = logging.getLogger(__name__)

from rwe.constants import *


def _create_tables(dump_file, tables_directoryectory):
    from rwe.tables import extract_and_render
    extract_and_render(dump_file, tables_directoryectory)


from rwe.exception import ExtractException
class TableException(ExtractException): pass


"""
Априорный список возможных окончаний.

Predefined set of possible inflexions.
"""
_inflexions = set([''])
"""
Априорный список возможных суффиксов.

Predefined set of possible suffixies.
"""
_suffixies = set()

def _load_set(set, set_file, replace=False):
    """
    Загружает априорный список морфем в переменную `set` из файла `dump_file`,
    удаляя мягкий и твёрдый знак, если `replace` установлен в True.

    Loads predefined set of morphemes into `set` from file `dump_file`,
    removing 'ь' and 'ъ' if `replace` is True.
    """
    with set_file: 
        for l in set_file:
            l = l.strip()
            if l == '' or l[0] == '#':
                continue
            if replace:
                l = l.replace('ь', '').replace('ъ', '')

            set.add(l)

def _load_sets(inflexions_file="data/inflexions", suffixies_file="data/suffixies"):
    """
    Загружает `_suffixies' и `_inflexions`.

    Loads `_suffixies` and `_inflexions`.
    """
    _load_set(_inflexions, inflexions_file)
    _load_set(_suffixies, suffixies_file, True)



def _segment_template_ending(ending):
    """
    Разбивает на морфемы конец слова из шаблона таблиц склонения/спряжения.

    Segments into morphemes word ending from declension/conjugation table template.
    """

    segmented_ending = [ending]

    check_for_inflexion = True
    ''' Постфиксы '''
    if len(segmented_ending[0]) >= 2:
        last_two_letters = segmented_ending[0][-2:]
        if last_two_letters == 'ся' or last_two_letters == 'сь':
            check_for_inflexion = len(segmented_ending[0]) > 2
            if check_for_inflexion:
                segmented_ending = [segmented_ending[0][:-2], 'частица_' + last_two_letters]
            else:
                segmented_ending[0] = 'частица_' + last_two_letters


    check_for_suffixies = False
    ''' Окончания '''
    if check_for_inflexion and segmented_ending[0] in _inflexions:
        segmented_ending[0] = 'оконч_' + segmented_ending[0]
        check_for_inflexion = False
    if check_for_inflexion and segmented_ending[0] not in _inflexions:
        check_for_suffixies = True
        for i in range(-3,0):
            if segmented_ending[0][i:] in _inflexions:
                ending_suffixies = segmented_ending[0][:i]
                segmented_ending[0] = 'оконч_' + segmented_ending[0][i:]
                segmented_ending.insert(0, ending_suffixies)
                break

    if check_for_suffixies:
        if segmented_ending[0] == 'ь':
            check_for_suffixies = False
            segmented_ending.pop(0)
        else:
            segmented_ending[0] = segmented_ending[0].replace('ь', '')

    if check_for_suffixies and segmented_ending[0] in _suffixies:
        segmented_ending[0] = 'суфф_' + segmented_ending[0]
        check_for_suffixies = False
    if check_for_suffixies and not segmented_ending[0] in _suffixies:
        ending_suffixies = segmented_ending[0]
        suffixies_segmentation_found = False
        for i in range(1,len(ending_suffixies)):
            if ending_suffixies[:i] in _suffixies and ending_suffixies[i:] in _suffixies:
                segmented_ending[0] = 'суфф_' + ending_suffixies[i:]
                segmented_ending.insert(0, 'суфф_' + ending_suffixies[:i])
                suffixies_segmentation_found = True
                break

        if not suffixies_segmentation_found:
            raise TableException(segmented_ending, ending)

    return ' '.join(segmented_ending)


# TODO check if native lazy loading availiable
def _template_form_generator(template_name, parameter, ending):
    def impl():
        try:
            segmented_ending = _segment_template_ending(ending)
            return (parameter, segmented_ending)
        except TableException as e:
            logger.info("Can't segment template %s ending %s %s: %s", template_name, parameter, ending, e.string)
            raise TableException(e.string, template_name, parameter, ending)

    return impl

class LazyDict(dict):

    def get(self, key, default=None):
        value = dict.get(self, key, default)
        if type(value) == dict and value != default:
            instantiated_value = set()
            for clojure in value.values():
                instantiated_value.add(clojure())

            value = instantiated_value
            self[key] = value

        return value

    def __getitem__(self, key):
        value = self.get(key)
        if value is None: raise KeyError(key)
        return value


def load_segmentation_table_templates(args):
    """
    Загружает шаблоны таблиц в словарь 'имя шаблона' -> 'список частичных разбиений'
    Частичных потому, что сейчас частично разбиение имеет вид:
        {{{#номер основы#}}} #разбиение конечной части слова из таблицы#

    `dump_file` требуется только если таблицы не были извлечены в файлы.


    Loads tables' templates into convenient dict 'template name' -> 'set of partial segmentations'.
    Partial in a sense that now segmentations are of form:
        {{{#stem identificator#}}} #segmented ending from table#

    `dump_file` is required if not yet tables were extracted in plain text files.
    """
    _load_sets(args.inflexions, args.suffixies)

    if not os.path.exists(args.tables_directory): 
        _create_tables(args.dump_file, args.tables_directory)

    segmentation_table_templates = LazyDict()
    for filename in os.listdir(args.tables_directory):
        if filename[-6:] != '.table':
            continue

        f = open(os.path.join(args.tables_directory, filename), 'r')
        lines = ''.join(f.readlines()).replace(stress, '')
        f.close()

        template_name = filename[:-6].replace('%', '/')

        templates = {}
        for match in re.finditer('(\{\{\{[^ ]+\}\}\})([а-яёй]*)', lines):
            if match.group(0) in templates:
                continue

            clojure = _template_form_generator(template_name, match.group(1), match.group(2))
            templates[match.group(0)] = clojure

        segmentation_table_templates[template_name] = templates

    return segmentation_table_templates
