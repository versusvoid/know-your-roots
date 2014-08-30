Augments for [Stanford CoreNLP](https://github.com/stanfordnlp/CoreNLP)
===============

Some additional classes for easing use of Stanford CRF classifier.

* [MorphoFeaturesFactory](MorphoFeaturesFactory.java) provides features for morpheme segmentations.
* [RussianConllSegmenter](RussianConllSegmenter.java) takes file in CoNLL dependency tree format, segments into morphemes words from *FORM* column and appends this morphemes as separate columns, i.e. each morpheme type gets it's own column.

Also example properties for MorphoFeaturesFactory and linguistic data it make use of.
