
import re

from rwe.exception import ExtractException
class YotException(ExtractException): pass

yot_vowels_mapping = {"э": "е", "у": "ю", "о": "ё", "а": "я"}

def replace_yot(base_form_segmentation):
    """
    Заменяет 'j' встречающийся в шаблоне {{{морфо}}} 
    на соответствующую комбинацию букв.

    Replaces accidentialy appearing in {{{морфо}}} template 'j' 
    with corresponding letters combination.
    """

    for i in range(len(base_form_segmentation)):
        part_type, part = base_form_segmentation[i]
        yot_pos = part.find('j')
        if yot_pos == -1: continue

        if part.count('j') > 1: 
            raise YotException('Too many yot: ', part, base_form_segmentation)

        if yot_pos != len(part) - 1:
            part = re.sub('j[эуоа]', lambda m: yot_vowels_mapping[m.group()[1]], part)

            if 'j' in part: 
                raise YotException('Unreplacable yot:', part, base_form_segmentation)

        elif i == len(base_form_segmentation) - 1:
            if len(part) < 2:
                raise YotException('Bad base form segmentation:', base_form_segmentation)

            if part[len(part) - 2] in 'уеыаоэяию':
                part = part.replace('j', 'й')
            elif part_type == 'оконч':
                part = part.replace('j', 'ь')
            else:
#               Здесь может быть мягкий знак, но мы на него пока кладём
                part = part.replace('j', '')

            base_form_segmentation[i] = part_type, part

        else:
            j = i + 1
            next_part_type, next_part = base_form_segmentation[j]

            next_part = re.sub('^[эуоа]', lambda m: yot_vowels_mapping[m.group()], next_part)
#           Здесь может быть мягкий знак, но мы на него пока кладём
            part = part.replace('j', '')

            base_form_segmentation[j] = next_part_type, next_part
            base_form_segmentation[i] = part_type, part


    return base_form_segmentation


