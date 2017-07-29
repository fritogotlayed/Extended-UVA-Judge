"""Module to assist with language standardization.

This module is to assist with mapping the problems submission language to a
language we can standardize against for the Judge code. For example: a user
could make a submission with "python", "py2" or "python2" as the language and
the judge will use "python2" as the submission language in dependent code.
"""
import extended_uva_judge.errors as errors

PYTHON2 = 'python2'
PYTHON3 = 'python3'
C_SHARP = 'c_sharp'
JAVA = 'java'

_LANG_MAP = {
    PYTHON2: PYTHON2,
    'python': PYTHON2,
    'py2': PYTHON2,
    PYTHON3: PYTHON3,
    'py3': PYTHON3,
    C_SHARP: C_SHARP,
    'csharp': C_SHARP,
    'cs': C_SHARP,
    JAVA: JAVA
}


def map_language(language):
    """Maps a language to a standardized string

    :param language: The language abbreviation to standardize
    :type language: str

    :return: The standardized language
    :rtype: str
    """
    val = _LANG_MAP.get(language)
    if val is None:
        raise errors.UnsupportedLanguageError(language)
    return val


def get_all_languages(lang_filter=None):
    """Gets available languages and their abbreviations.

    :param lang_filter: The language to filter results to.
    :type lang_filter: str

    :return: Dictionary of standardized languages with all accepted
             abbreviations.
    :rtype: dict
    """
    languages = {}
    for key in _LANG_MAP:
        normalized_key = map_language(key)
        if lang_filter is None or normalized_key in lang_filter:
            if languages.get(normalized_key) is None:
                languages[normalized_key] = []
            languages[normalized_key].append(key)

    return languages
