from typing import Optional, Union, Text, List
from fontTools.misc.py23 import PY3


try:
    long
except NameError:
    long = int


OptText = Optional[Text]
Integer = int if PY3 else Union[int, long]
Number = Union[float, Integer]
OptInteger = Optional[Integer]
OptFloat = Optional[float]
OptNumber = Optional[Number]
OptBool = Optional[bool]

IntList = List[Integer]
OptIntList = Optional[IntList]
NumList = List[Number]
OptNumList = Optional[NumList]
