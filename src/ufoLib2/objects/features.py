import attr


@attr.s(auto_attribs=True, slots=True)
class Features:
    text: str = ""

    def __bool__(self) -> bool:
        return bool(self.text)

    def __str__(self) -> str:
        return self.text
