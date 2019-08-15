import attr


@attr.s(slots=True)
class Features(object):
    text = attr.ib(default="", type=str)

    def __bool__(self):
        return bool(self.text)

    def __str__(self):
        return self.text
