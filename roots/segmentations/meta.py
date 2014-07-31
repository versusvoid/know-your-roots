"""
Функции для извлечения мета-информации (вызвы шаблонов) из дампа
русского викисловаря для дальнейшего извлечения состава слов.

Functions for extraction of meta-information (templates invocations)
from ruwiktionary dump for later extraction of segmentations.
"""

import xml.etree.ElementTree as ET
import re
import sys
import os
import traceback


import logging
logger = logging.getLogger(__name__)



from rwe.constants import *

def _extract_template(text, template_start_re):
    """
    Извлекает вызов шаблона, который начинается с строки подходящей под
    регулярное выражение `template_start_re`, если такой вообще есть в `text`.

    Extracts whole template invocation with beginning matching `template_start_re`,
    if such exists in `text`.
    """
    template = re.search(template_start_re, text)
    if not template:
        return

    text = list(text)
    n = 1
    i = template.start() + 1
    while i < len(text) and n > 0:
        if text[i] == '{':
            n = n + 1
        if text[i] == '}':
            n = n - 1
        if n > 2 and text[i] == '|':
            text[i] = '№'
        i = i + 1

    if n != 0:
        return

    return ''.join(text[template.start():i])


lang = re.compile('{{-[a-z]{2,3}-}}')

english_to_russian = {'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'x': 'х'}
def _handle_page(text, word, queue):
    word = word.replace(stress, '')
    if not text or not re.match('[А-ЯЁ]?[а-яё]+', word):
        logger.debug('Skipping %s cause empty or not a russian word', word)
        return
    word = word.lower()

    ru = re.search('{{-ru-}}', text)
    if not ru:
        logger.debug('Skipping %s cause no -ru-', word)
        return

    text = text[ru.start() + len('{{-ru-}}'):]

    other = lang.search(text)
    if other:
        text = text[:other.start()]

#   Enjoy your unicode
    text = text.replace(stress, '').replace(stress2, '')

    morf = _extract_template(text, '{{морфо')
    if morf is None:
        logger.debug('Skipping %s cause no morfs', word)
        return

    morf = morf.lower()
    morf = re.subn('(\n|\t| )+', '', morf)[0]
    morf = re.subn('[ceoxa]', lambda m: english_to_russian[m.group()], morf)[0]
#   Enjoy your unicode
    morf = morf.replace('ʲ', 'j')

    if re.search('[^}{а-яёйj1-5|=-]', morf):
        logger.info('Skipping  %s %s cause strange symbols', word, morf)
        return
    if re.match('{{морфо(\|+[а-я-]+[1-5]?=)+}}', morf) or re.match('{{морфо\|+}}', morf):
        logger.debug('Skipping %s %s cause empty', word, morf)
        return

    table_template_call = _extract_template(text, '{{(прич|сущ|гл|мест|прил|числ) ru ')
    if table_template_call is None:
        logger.debug('No table call for %s', word)
        return


    template_name = table_template_call[2:table_template_call.index('|')].strip()
    template_params = table_template_call[2:-2].lower()
    template_params = re.subn('(\n|\t| )+', '', template_params)[0]
    template_params = re.subn('[ceoxa]', lambda m: english_to_russian[m.group()], template_params)[0]
    template_params = template_params.split('|')[1:]
    filtered_params = filter(lambda s: re.match('основа[1-5]?=[а-яёй-]+', s) or re.match('[а-яёй-]+$', s), template_params)
    filtered_params = list(filtered_params)
    if len(filtered_params) == 0:
        logger.debug('Skipping %s cause no stems in table template call', word)
        return

    queue.put( (morf, template_name, filtered_params) )



def extract_meta_segmentations(dump_file):
    
    context = ET.iterparse(dump_file, events=("start", "end"))
    context = iter(context)
    event, root = next(context)

    page = False
    word = ''
    text = ''

    import queue
    import concurrent.futures

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    extracted_queue = queue.Queue()

    count = 0

    for event, elem in context:
        if elem.tag == page_tag:
            if event == 'start':
                page = True
                continue
            else:
                executor.submit(_handle_page, text, word, extracted_queue)
    
        if page and event == "end" and elem.tag == title_tag:
            word = elem.text

        if page and event == 'end' and elem.tag == text_tag:
            text = elem.text

        if event == 'end':
            elem.clear()

    root.clear()

    logger.info('Done reading xml dump for meta-segmentations')

    try:
        while True:
            extracted = extracted_queue.get(timeout=2)
            yield extracted
            
            count += 1
            if count % 1000 == 0:
                logger.debug('Metas: %d', count)

    except queue.Empty: pass

    executor.shutdown()


def main(args):

    for morf, template_name, filtered_params in extract_meta_segmentations(args.dump_file):
        print(morf, template_name, *filtered_params, sep=';', file=args.output)

    args.output.close()
