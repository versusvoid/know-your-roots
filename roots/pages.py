"""
Модуль позволяет извлекать и, по необходимости, сохранять в виде
отдельных файлов страницы из дампа Wiktionary. Хотя конкретно этот
модуль не завязан на Wiktionary и сможет испольнить свои обязанности
на любом дампе в формате экспорта MediaWiki.

Module is devoted to extracting and optionaly saving as separate files
pages from Wiktionary dump. It also may be any dump in MediaWiki
export format.

"""

import xml.etree.ElementTree as ET
import re

import os
import sys

from rwe.constants import *

def handle_page(pattern, page_content, page_title, output_directory):
    if not pattern.match(page_title):
        return

    if output_directory is None:
        return page_title
    else:
        dump_file = os.path.join(output_directory, page_title.replace('/', '-').replace(' ', '_'))
        if not os.path.exists(os.path.output_directory(dump_file)):
            os.makedirs(os.path.output_directory(dump_file))

        f = open(dump_file, 'a')
        f.write(page_content)
        f.close()

        return (page_title, dump_file)

def extract(pattern, dump_file='ruwiktionary.xml', output_directory=None):
    """Извлекает все страницы с заголовком удовлетворяющим `pattern` из дампа `dump_file`.
    Сохраняет их если указан `output_directory` и возвращает список кортежей (заголовок страницы, имя файла),
    иначе просто возвращает список подходящих заголовков.
    
    Extract pages with title matching `pattern` regexp from dump `dump_file`.
    If `output_directory` is `None` then do nothing except return list of pages' names,
    otherwise extract page to file and return list of pairs (page title, file name).

    """
    context = ET.iterparse(dump_file, events=("start", "end"))
    context = iter(context)
    event, root = next(context)

    page = False
    page_title = ''
    page_content = ''

    pattern = re.compile(pattern)

    extracted = []

    for event, elem in context:
        if elem.tag == page_tag:
            if event == 'start':
                page = True
                continue
            else:
                try:
                    extracted_page = handle_page(pattern, page_content, page_title, output_directory)
                    if extracted_page is not None:
                        extracted.append(extracted_page)
                except:
                    print(page_title, page_content)

        if page and event == "end" and elem.tag == title_tag:
            page_title = elem.text

        if page and event == 'end' and elem.tag == text_tag:
            page_content = elem.text

        if event == 'end':
            elem.clear()

    root.clear()
    return extracted


def main(args):
    print(*extract(args.pattern, args.dump_file, args.output_directory))
