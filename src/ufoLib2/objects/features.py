import attr


@attr.s(auto_attribs=True, slots=True)
class Features:
    text: str = ""

    def __bool__(self):
        return bool(self.text)

    def __str__(self):
        return self.text
