"""
Различные константы используемые при работе с дампом русского викисловаря.

Different constants conserning ruwiktionary.
"""

"""
Специальный символ для отображения ударения в словах. Удаляется из
входных данных во время извлечения мета-информации.

Unicode symbol used for set stress on letter. Removed from input
during extraction.
"""
stress = '́'
stress2 = '̀'

"""
Пространство имён формата экспорта MediaWiki в виде, использемом в ElementTree.

MediaWiki export namespace as it appears in ElementTree tags.
"""
namespace = '{http://www.mediawiki.org/xml/export-0.8/}'
page_tag  = namespace + 'page'
title_tag = namespace + 'title'
text_tag  = namespace + 'text'
