from __future__ import absolute_import, unicode_literals
import attr
from fontTools.misc.py23 import tounicode, unicode


@attr.s(slots=True)
class Features(object):
    text = attr.ib(default="", converter=tounicode, type=unicode)

    def __bool__(self):
        return bool(self.text)

    __nonzero__ = __bool__

    def __str__(self):
        return self.text
