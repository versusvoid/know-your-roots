know-your-roots
===============

Extract word to morphemes segmentations from [russian wiktionary](http://ru.wiktionary.org).


# Usage

## Prerequisites

* ruwiktionary dump ([grub](http://dumps.wikimedia.org/ruwiktionary/latest/ruwiktionary-latest-pages-articles-multistream.xml.bz2) one)
* Python 3
* Internet connection capable of downloading <1mb data from ru.wiktionary.org
* Patience

When everything is ready, do three simple steps:

1. Extract dump
2. `$ python3 -m roots.main -D *path to your extracted dump* `
3. Wait

# Algorithm

Whole process divided into three steps:

1. Find in dump, request HTML render from ru.wiktionary.org and save in plain form all declension/conjugation tables (e.g. [Шаблон:сущ ru f ina 1d](http://ru.wiktionary.org/wiki/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD:%D1%81%D1%83%D1%89_ru_f_ina_1d)). This step is placed in [tables.py](roots/tables.py).
2. Find in dump and extract meta-information required for segmentations extraction. This includes 'invocations' of  [{{{морфо}}}](https://ru.wiktionary.org/wiki/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD:%D0%BC%D0%BE%D1%80%D1%84%D0%BE) and declension/conjugation table templates. This simple step dwells in [meta.py](roots/segmentations/meta.py).
3. Using information from previous two steps extract base form segmentations and align it with derived forms. This functionality is scattered across whole [roots.segmentations](roots/segmentations) module.


All three steps can be executed independently. Refer to
```sh
$ python3 -m roots.main -h
```
for further information.

You can also pass `-d` flag to enable debugging mode and stop on every failed extraction. 
I'll probably extend it to stop on every extraction some time soon.

---
For now it capable of extraction ~400k segmentations. Yes, data is VERY noisy, but I'm working on it, I swear!
