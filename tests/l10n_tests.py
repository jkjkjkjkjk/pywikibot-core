# -*- coding: utf-8 -*-
"""Test valid templates."""
#
# (C) Pywikibot team, 2015-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import os

import pywikibot
from pywikibot import i18n
from pywikibot.textlib import extract_templates_and_params_regex_simple

from tests.aspects import unittest, MetaTestCaseClass, TestCase
from tests.utils import add_metaclass

PACKAGES = (
    'redirect-broken-redirect-template',  # speedy deletion template
    'archivebot-archiveheader',  # archive header template
)


class TestValidTemplateMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(site):

            def test_template(self):
                """Test validity of template."""
                lang = site.lang
                if lang not in keys:
                    return
                msg = i18n.twtranslate(lang, package, fallback=False)
                if msg:
                    # check whether the message contains a template
                    templates = extract_templates_and_params_regex_simple(msg)
                    self.assertIsInstance(templates, list)
                    self.assertIsNotEmpty(templates)

                    # known problem
                    if site.code == 'simple':
                        raise unittest.SkipTest(
                            "'simple' wiki has 'en' language code but "
                            'missing template. Must be solved by the '
                            'corresponding script.')
                    # check whether template exists
                    title = templates[0][0]
                    page = pywikibot.Page(site, title, ns=10)
                    self.assertTrue(
                        page.exists(),
                        msg='Invalid L10N in package "{package}"\n'
                        'template "{title}" does not exist for lang '
                        '"{site.lang}" on site "{site}"'
                        .format(package=package, title=title, site=site))

            return test_template

        # create test methods for package messages processed by unittest
        site = pywikibot.Site(dct['code'], dct['family'])
        codes = site.family.languages_by_size
        del site
        for package in PACKAGES:
            keys = i18n.twget_keys(package)
            for code in codes:
                current_site = pywikibot.Site(code, dct['family'])
                test_name = ('test_{}_{}'
                             .format(package, code)).replace('-', '_')
                cls.add_method(
                    dct, test_name, test_method(current_site),
                    doc_suffix='{0} and language {1}'.format(
                        package, code))

        return super(TestValidTemplateMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestValidTemplate(TestCase):

    """Test cases L10N message templates processed by unittest."""

    __metaclass__ = TestValidTemplateMeta

    family = 'wikipedia'
    code = 'en'

    @classmethod
    def setUpClass(cls):
        """Skip test gracefully if i18n package is missing."""
        super(TestValidTemplate, cls).setUpClass()
        if not i18n.messages_available():
            raise unittest.SkipTest("i18n messages package '{}' not available."
                                    .format(i18n._messages_package_name))


class TestSites(TestCase):

    """Other test L10N cases processed by unittest."""

    family = 'wikipedia'
    code = 'en'

    def test_valid_sites(self):
        """Test whether language key has a corresponding site."""
        codes = self.site.family.languages_by_size
        languages = {pywikibot.Site(code, self.family).lang for code in codes}
        # langs used by foreign wikis
        languages.update(('pt-br', 'zh-tw'))
        for package in PACKAGES:
            keys = i18n.twget_keys(package)
            for key in keys:
                with self.subTest(package=package, key=key):
                    self.assertIn(key, languages,
                                  "json key '{}' is not a site language"
                                  .format(key))


def setUpModule():  # noqa: N802
    """Skip Travis tests if PYWIKIBOT_NO_L10N_TESTS variable is set."""
    if os.environ.get('PYWIKIBOT_NO_L10N_TESTS', '0') == '1':
        raise unittest.SkipTest('L10N tests disabled.')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
