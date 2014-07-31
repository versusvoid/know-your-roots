#!/usr/bin/env python

import operator
import os
import re
import sys
import queue
import concurrent.futures

import logging
logger = logging.getLogger(__name__)

from rwe.exception import ExtractException
import rwe.segmentations.meta as meta
import rwe.segmentations.tables as tables
import rwe.segmentations.base_form as base_form
import rwe.segmentations.stems

debug_mode = False

def render_template(template, parameters):
    """
    Подставляет полученные ранее разбиения в шаблон, получая на выходе
    полные разбиения форм слова на морфемы.
    
    Renders preprocessed declension/conjugation template using segmented stems,
    resulting in full word's forms segmentation into morphemes.
    """
    result = []
    for parameter, inflexion in template:
        value = None
        split_index = parameter.find('|')
        if split_index > -1:
            if parameter[:split_index] + '}}}' in parameters:
                value = parameters[parameter[:split_index] + '}}}']
            else:
                value = parameters[parameter[split_index + 1 : parameter.index('}', split_index) + 3]]
        else:
            value = parameters[parameter]

        result.append(value + ' ' + inflexion)

    return result

def check_segmentation(segmentation):
    match = re.match('\w+_[\w-]+( \w+_[\w-]*)* *', segmentation)
    if not match or match.end(0) != len(segmentation): raise ValueError("'" + segmentation + "'")



def read_metas(metas_file):
    """
    Считывает мета-информацию для разбиений из файла.

    Reads meta-segmentations from file.
    """
    for l in metas_file:
        morfo, template_name, *stems = l.strip().split(';')
        yield (morfo, template_name, stems)

def segment_word(morfo, stems, template, extracted_queue):
    """
    Высчитывает разбиения форм слова основываясь на разбиении начальной формы
    и таблицы склонения/спряжения.

    Computes word forms' segmentations from word normal form segmentation 
    ({{{морфо}}} template) and declension/conjugation table template.
    """
    
    try:

        base_form_segmentation = base_form.extract_base_form_segmentation(morfo)
    except ExtractException as e:
        logger.info("Can't extract segmentation from morfo %s: %s", morfo, e.string)
        if debug_mode: input()
        return

    if not base_form.check_for_root_presence(base_form_segmentation):
        logger.debug('No root for morfo %s', morfo)
        if debug_mode: input()
        return

    word = ''.join(map(operator.itemgetter(1), base_form_segmentation))

    try:

        segmented_stems = rwe.segmentations.stems.segment_additional_stems(base_form_segmentation, stems)
        if segmented_stems is None:
            logger.debug('No stems segmentation form %s', word)
            return
        stems_dict = rwe.segmentations.stems.fill_stems_dict(segmented_stems)
        segmentations = render_template(template, stems_dict)

    except ExtractException as e:
        logger.info("Can't extract segmentations for word %s: %s", word, e.string)
        if debug_mode: input()
        return

    for segmentation in segmentations:
        check_segmentation(segmentation)
        extracted_queue.put(segmentation)


def writer(extracted_queue, output):

    metas_read = False
    while True:
        try:
            segmentation = extracted_queue.get(timeout=2)
            if segmentation == 'metas read':
                metas_read = True
            else:
                print(segmentation, file=output)
                output.flush()
        except queue.Empty:
            if metas_read: break



def main(args):
    segmentation_table_templates = tables.load_segmentation_table_templates(args)

    metas = None
    if args.meta_segmentations is not None:
        metas = read_metas(args.meta_segmentations)
    else:
        metas = meta.extract_meta_segmentations(args.dump_file)

    debug_mode = args.debug

    if debug_mode:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    else:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

    extracted_queue = queue.Queue()

    executor.submit(writer, extracted_queue, args.output)

    for morfo, template_name, stems in metas:
        try:
            template = segmentation_table_templates.get(template_name)
            if not template:
                logger.info('No template %s from word %s', template_name, morfo)
            if debug_mode:
                segment_word(morfo, stems, template, extracted_queue)
            else:
                executor.submit(segment_word, morfo, stems, template, extracted_queue)
        except ExtractException as e:
            logger.info("Can't instantiate template: %s", e.string)
            segmentation_table_templates.pop(template_name)
            if debug_mode: input()

    logger.info('all metas read')

    extracted_queue.put('metas read')
    executor.shutdown()

    args.output.close()
