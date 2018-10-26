try:
    from collections.abc import Mapping, MutableMapping
except ImportError:
    from collections import Mapping, MutableMapping
try:
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec


# sentinel value to signal a "lazy" object hasn't been loaded yet
_NOT_LOADED = object()


class DataStore(MutableMapping):
    _fields = ("data",)
    __slots__ = _fields + ("_reader", "_scheduledForDeletion")

    listdir = None
    readf = None
    writef = None
    deletef = None

    def __init__(self, data=None):
        self.data = {} if data is None else data
        self._reader = None
        self._scheduledForDeletion = set()

    @classmethod
    def read(cls, reader, lazy=True):
        self = cls()
        for fileName in cls.listdir(reader):
            if lazy:
                self.data[fileName] = _NOT_LOADED
            else:
                self.data[fileName] = cls.readf(reader, fileName)
        if lazy:
            self._reader = reader
        return self

    # MutableMapping methods

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, fileName):
        if self.data[fileName] is _NOT_LOADED:
            self.data[fileName] = self.__class__.readf(self._reader, fileName)
        return self.data[fileName]

    def __setitem__(self, fileName, data):
        # should we forbid overwrite?
        self.data[fileName] = data
        if fileName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(fileName)

    def __delitem__(self, fileName):
        del self.data[fileName]
        self._scheduledForDeletion.add(fileName)

    def __repr__(self):
        n = len(self.data)
        return "<{}.{} ({}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            "empty" if n == 0 else "{} file{}".format(n, "s" if n > 1 else ""),
            hex(id(self)),
        )

    def write(self, writer, saveAs=None):
        if saveAs is None:
            saveAs = self._reader is not writer
        # if in-place, remove deleted data
        if not saveAs:
            for fileName in self._scheduledForDeletion:
                self.__class__.deletef(writer, fileName)
        # write data
        for fileName, data in self.data.items():
            if data is _NOT_LOADED:
                if saveAs:
                    data = self.__class__.readf(self._reader, fileName)
                else:
                    continue
            self.__class__.writef(writer, fileName, data)
        self._scheduledForDeletion = set()
        if saveAs:
            # all data was read by now, ref to reader no longer needed
            self._reader = None

    @property
    def fileNames(self):
        return list(self.data.keys())


class AttrReprMixin(object):
    def __repr__(self):
        init = getargspec(self.__init__)
        dflt = dict(
            list(zip(reversed(init.args), reversed(init.defaults or ())))
        )
        keys = self._fields
        items = (
            "{}={!r}".format(k.lstrip("_"), getattr(self, k))
            for k in keys
            if getattr(self, k) != dflt.get(k)
        )
        return "{}({})".format(type(self).__name__, ", ".join(items))


class AttrDictMixin(AttrReprMixin, Mapping):
    """ Read attribute values using mapping interface. For use with Anchors and
    Guidelines classes, where client code expects them to behave as dict.
    """

    def __getitem__(self, key):
        try:
            value = getattr(self, key)
        except AttributeError:
            raise KeyError(key)
        if value is None:
            raise KeyError(key)
        return value

    def __iter__(self):
        for key in self._fields:
            if getattr(self, key) is not None:
                yield key

    def __len__(self):
        return sum(1 for _ in self)
