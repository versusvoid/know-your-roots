
if __name__ == '__main__':
    import argparse
    import sys
    import logging

    import rwe.pages
    import rwe.tables
    import rwe.segmentations.meta
    import rwe.segmentations.annotated

    parser = argparse.ArgumentParser(description='Extracts annotated (type of morpheme) segmentations of russian words from ruwiktionary.')
    parser.add_argument('-D', '--dump-file', type=str, default='ruwiktionary.xml', help='ruwiktionary dump file (%(default)s)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='verbose (repeat for more output)')
    parser.add_argument('-L', '--log', type=argparse.FileType('w'), default=sys.stderr, help='file to log debug messages (%(default)s)')
    parser.add_argument('-O', '--output', type=argparse.FileType('w'), default='segmentations.txt', help='file to output segmentations (%(default)s)')
    parser.add_argument('-A', '--address', type=str, default='ru.wiktionary.org', help='address of mediawiki with ruwiktionary data (%(default)s).\nRequired if no tables were previously extracted')
    parser.add_argument('-T', '--tables-directory', type=str, default='tables', help='directory to load from or put extracted tables into if not already extracted (%(default)s)')
    parser.add_argument('-M', '--meta-segmentations', type=argparse.FileType('r'), help='file with meta-segmentations (defaults to %(default)s meaning extract them on the go)')
    parser.add_argument('-I', '--inflexions', type=argparse.FileType('r'), default='inflexions', help='file with possible inflexions list (%(default)s)')
    parser.add_argument('-S', '--suffixies', type=argparse.FileType('r'), default='suffixies', help='file with possible suffixies list (%(default)s)')
    parser.add_argument('--debug', action='store_true', default=False, help='enable debug mode')


    subparsers = parser.add_subparsers()


    pages = subparsers.add_parser('pages', help='extract pages from mediawiki dump')
    pages.set_defaults(func=rwe.pages.main)
    pages.add_argument('pattern', type=str, help="regexp to match pages' titles")
    pages.add_argument('-O', '--output-directory', type=str, default='pages', help='directory to put extracted pages into (if undefined - only print matching titles)')


    tables = subparsers.add_parser('tables', help="extract declesion/conjugation tables' templates for russian language")
    tables.set_defaults(func=rwe.tables.main)
    tables.add_argument('-H', '--save-html', action='store_true', help='save rendered html under same directory? (%(default)s)')


    metas = subparsers.add_parser('metas', help="extract segmentations meta-information", description="extract templates calls and parameters required to extract fully-annotated segmentations")
    metas.set_defaults(func=rwe.segmentations.meta.main)


    args = parser.parse_args()

    logging_level = logging.WARN
    if args.verbose > 1:
        logging_level = logging.DEBUG
    elif args.verbose > 0:
        logging_level = logging.INFO

    logger = logging.getLogger('rwe')
    logger.setLevel(logging_level)
    
    fh = logging.StreamHandler(args.log)
    fh.setLevel(logging_level)

    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    if 'func' not in args:

        rwe.segmentations.annotated.main(args)
    else:
        args.func(args)
