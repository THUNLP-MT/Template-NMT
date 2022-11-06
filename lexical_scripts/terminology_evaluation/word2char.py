import sys
import re


_UCODE_RANGES = [
    (u'\u3400', u'\u4db5'),  # CJK Unified Ideographs Extension A, release 3.0
    (u'\u4e00', u'\u9fa5'),  # CJK Unified Ideographs, release 1.1
    (u'\u9fa6', u'\u9fbb'),  # CJK Unified Ideographs, release 4.1
    (u'\uf900', u'\ufa2d'),  # CJK Compatibility Ideographs, release 1.1
    (u'\ufa30', u'\ufa6a'),  # CJK Compatibility Ideographs, release 3.2
    (u'\ufa70', u'\ufad9'),  # CJK Compatibility Ideographs, release 4.1
    (u'\u20000', u'\u2a6d6'),  # (UTF16) CJK Unified Ideographs Extension B, release 3.1
    (u'\u2f800', u'\u2fa1d'),  # (UTF16) CJK Compatibility Supplement, release 3.1
    (u'\uff00', u'\uffef'),  # Full width ASCII, full width of English punctuation,
                             # half width Katakana, half wide half width kana, Korean alphabet
    (u'\u2e80', u'\u2eff'),  # CJK Radicals Supplement
    (u'\u3000', u'\u303f'),  # CJK punctuation mark
    (u'\u31c0', u'\u31ef'),  # CJK stroke
    (u'\u2f00', u'\u2fdf'),  # Kangxi Radicals
    (u'\u2ff0', u'\u2fff'),  # Chinese character structure
    (u'\u3100', u'\u312f'),  # Phonetic symbols
    (u'\u31a0', u'\u31bf'),  # Phonetic symbols (Taiwanese and Hakka expansion)
    (u'\ufe10', u'\ufe1f'),
    (u'\ufe30', u'\ufe4f'),
    (u'\u2600', u'\u26ff'),
    (u'\u2700', u'\u27bf'),
    (u'\u3200', u'\u32ff'),
    (u'\u3300', u'\u33ff'),
]


_re_list = [
    # language-dependent part (assuming Western languages)
    (re.compile(r'([\{-\~\[-\` -\&\(-\+\:-\@\/])'), r' \1 '),
    # tokenize period and comma unless preceded by a digit
    (re.compile(r'([^0-9])([\.,])'), r'\1 \2 '),
    # tokenize period and comma unless followed by a digit
    (re.compile(r'([\.,])([^0-9])'), r' \1 \2'),
    # tokenize dash when preceded by a digit
    (re.compile(r'([0-9])(-)'), r'\1 \2 '),
    # one space only between words
    # NOTE: Doing this in Python (below) is faster
    # (re.compile(r'\s+'), r' '),
]


def _is_chinese_char(uchar):
    """
    :param uchar: input char in unicode
    :return: whether the input char is a Chinese character.
    """
    for start, end in _UCODE_RANGES:
        if start <= uchar <= end:
            return True
    return False


for line in sys.stdin:
	line = line.strip()
	line_in_chars = ""
	for char in line:
		if _is_chinese_char(char):
			line_in_chars += " "
			line_in_chars += char
			line_in_chars += " "
		else:
			line_in_chars += char
	for (_re, repl) in _re_list:
		line_in_chars = _re.sub(repl, line_in_chars)
	print(' '.join(line_in_chars.split()))