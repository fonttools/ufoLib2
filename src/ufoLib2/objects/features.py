from typing import Text
import attr


@attr.s(slots=True)
class Features(object):
    text = attr.ib(default="", type=Text)

    def __bool__(self):
        return bool(self.text)

    def __str__(self):
        return self.text
