"""
Модуль предназначен для извлечения в простом и удобном виде шаблонов таблиц 
склонения и спряжения из русского викисловаря. Имена шаблонов извлекаются 
из дампа, их рендер в html запрашивается у сервера и преобразуется в 
простейшую псевдографику.

Module is devoted to extraction of conjugation and declension tamplate tables
and their rendering to plain text form.
"""

import re
import os
import sys
import xml.etree.ElementTree as ET

import http.client
import urllib.parse

import rwe.pages

# !!! NOTE Шаблон:прил ru 2a has two templates in one cell
def render(template_name, text, output_directory):
    """
    Преобразует и сохраняет html табличку в простом виде.
    
    Converts and saves html table as plain text table.
    """
    parser = ET.XMLPullParser(events=("start", "end"))
    parser.feed('<fakeroot>')
    parser.feed(text)

    dump_file = os.path.join(output_directory, template_name.replace('Шаблон:', '').replace('/', '%') + '.table')
    of = open(dump_file, 'w')

    table = False

    try:
        for event, elem in parser.read_events():
            if event == 'start' and elem.tag == 'table' and 'style' in elem.attrib and re.match('float *: *right;', elem.attrib['style']):
                table = True

            if table and event == 'end' and elem.tag == 'table':
                break

            if table and event == 'end' and elem.tag == 'tr':
                print('', file=of)

            if table and event == 'end' and (elem.tag == 'th' or elem.tag == 'td'):
                text = elem.text
                if text is None:
                    a = elem.find('a')
                    if a is not None: text = a.text

                if text is not None:
                    print(text.strip(), '|', end=' ', file=of)

            if not table and event == 'end':
                elem.clear()
    except ET.ParseError as e:
        print(e)
        os.remove(dump_file)
        exit(1)

    of.close()


def extract_and_render(dump_file, output_directory, address, save_html=False):
    """
    Находит таблицы склонения и спряжения в дампе русского викисловаря, запрашивает их 
    рендер у сервера и сохраняет их по файлам в упрощённом виде.

    Finds declension and conjugation tables in ruwiktionary dump, requests their render
    from server and save in plain text form.
    """

    if not os.path.isdir(output_directory):
        if os.path.exists(output_directory): 
            raise Exception('Tables directory "{}" exists but is not directory'.format(output_directory))

        os.mkdir(output_directory)

    print('Parsing wiktionary dump for templates, be patient')
    template_names = rwe.pages.extract('Шаблон:(прич|сущ|гл|мест|прил|числ) ru', dump_file)
    print('Templates extracted:', *template_names, sep='\n')

    connection = http.client.HTTPConnection(address)
#    connection = http.client.HTTPSConnection("proxy", 3128)
#    connection.set_tunnel(address)
    for template_name in template_names:
        params = {
            'action': 'render',
            'title': template_name
        }
        print('Rendering html for', template_name)
        connection.request('GET', '/w/index.php?{}'.format(urllib.parse.urlencode(params)))
        r = connection.getresponse()
        if r.status != 200:
            print("Can't get", template_name, "template from wiktionary =\\")
            continue

        text = r.read().decode()

        if save_html:
            with open(os.path.join(output_directory, template_name.replace('Шаблон:', '').replace('/', '%') + '.html'), 'w') as f:
                print(text, file=f)

        render(template_name, text, output_directory)

    connection.close()


def main(args):
    extract_and_render(args.dump_file, args.output_directory, args.address, args.save_html)
