
import operator

from rwe.exception import ExtractException
class StemException(ExtractException): pass

import logging
logger = logging.getLogger(__name__)


def split_stems(stems_with_names, replace=False):
    for i, stem in enumerate(stems_with_names):
        if '=' in stem:
            name, stem = stem.split('=')
            if replace: stem = stem.replace('ь', '').replace('ъ', '')
            stems_with_names[i] = (name, stem)

    return stems_with_names

def segment_additional_stem(stem, base_form_segmentation):
    """
    Разбивает дополнительную основу для шаблонов таблиц склонения/спряжения,
    основываясь на добытом из шаблона {{{морфо}}} разбиения начальной формы слова.

    Segments additional stem used in declension/conjugation table template,
    taking base from segmentation from {{{морфо}}} template as basis.
    """
    original_stem = stem

    segmentation = []
    for part_type, part in base_form_segmentation:
        assert type(part_type) == str
        assert type(stem) == str

        if stem == '' and part_type == 'оконч':
            break

        if stem[:len(part)] == part:
            segmentation.append((part_type, part))
            stem = stem[len(part):]
        elif part_type == 'суфф':
            if len(part) > 0 and len(stem) > 0 and abs(len(part) - len(stem)) >= 3:
                raise ExtractException(part, stem, segmentation, base_form_segmentation)
            segmentation.append((part_type, stem))
            stem = ''
            break
        elif part_type == 'корень' and part[:len(stem)] == stem:
            segmentation.append((part_type, stem))
            stem = ''
            break
        else:
            logger.info('Cannot align stem %s to segmentation %s', original_stem, base_form_segmentation)
            return

    if stem != '':
        logger.info("Can't fully segment stem %s: %s", original_stem, segmentation)
        return

    return segmentation

def segment_additional_stems(base_form_segmentation, stems):
    base_form = ''.join(map(operator.itemgetter(1), base_form_segmentation))
    base_stem_found = False

    stems = split_stems(stems, True)
    new_stems = []
    for i, stem in enumerate(stems):
        name = None
        if type(stem) == tuple:
            name, stem = stem

        if base_form[:len(stem)] == stem:
            base_stem_found = True 
        
        segmentation = segment_additional_stem(stem, base_form_segmentation)
        if segmentation is None:
            logger.debug("Can't segment stem %s of %s", stem, stems)
            return

        stem = ' '.join(map(lambda p: p[0] + '_' + p[1], segmentation))
        if name is None:
            new_stems.append(stem)
        else:
            new_stems.append('{}={}'.format(name, stem))

    if not base_stem_found:
        logger.info("Can't find base stem %s in stems %s", base_form_segmentation, stems)
        return

    return new_stems


def fill_stems_dict(stems):
    """ 
    Переводит список основ вроде
        основа=мушк;основа1=мушек 
    или
        мушк;мушек
    в таблицу 
        {'{{{1}}}': 'мушк', '{{{основа}}}': 'мушк',...}
    для использования в шаблоне таблицы склонения/спряжения.

    Transforms list of stems from form:
        основа=мушк;основа1=мушек 
    or
        мушк;мушек
    into dict 
        {'{{{1}}}': 'мушк', '{{{основа}}}': 'мушк',...}
    for declension/conjugation table template.
    """
    result = {}
    i = 1
    for stem in split_stems(stems):
        value = stem
        if type(stem) == tuple:
            name, value = stem
            result['{{{' + name + '}}}'] = value
        result['{{{' + str(i) + '}}}'] = value
        i += 1

    if '{{{основа1}}}' in result and not '{{{основа}}}' in result:
        result['{{{основа}}}'] = result['{{{основа1}}}']
    if '{{{основа}}}' in result and not '{{{основа1}}}' in result:
        result['{{{основа1}}}'] = result['{{{основа}}}']

    return result

