import extended_uva_judge.errors as errors

PYTHON2 = 'python2'
PYTHON3 = 'python3'
C_SHARP = 'c_sharp'
JAVA = 'java'

_lang_map = {
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
    val = _lang_map.get(language)
    if val is None:
        raise errors.UnsupportedLanguageError(language)
    return val


def get_all_languages(lang_filter=None):
    languages = {}
    for key in _lang_map.keys():
        normalized_key = map_language(key)
        if lang_filter is None or normalized_key in lang_filter:
            if languages.get(normalized_key) is None:
                languages[normalized_key] = []
            languages[normalized_key].append(key)

    return languages
