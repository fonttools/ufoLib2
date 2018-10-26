from __future__ import absolute_import, unicode_literals
from fontTools.misc.py23 import tounicode


class Features(object):
    __slots__ = _fields = ("text",)

    def __init__(self, text=""):
        self.text = tounicode(text)

    def __bool__(self):
        return bool(self.text)

    __nonzero__ = __bool__

    def __str__(self):
        return self.text
