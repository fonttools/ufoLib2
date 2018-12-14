import attr

try:
    from collections.abc import Mapping, MutableMapping
except ImportError:
    from collections import Mapping, MutableMapping


# sentinel value to signal a "lazy" object hasn't been loaded yet
_NOT_LOADED = object()


@attr.s(slots=True, repr=False)
class DataStore(MutableMapping):
    listdir = None
    readf = None
    writef = None
    deletef = None

    _data = attr.ib(default=attr.Factory(dict), type=dict)

    _reader = attr.ib(default=None, init=False, repr=False)
    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, repr=False
    )

    @classmethod
    def read(cls, reader, lazy=True):
        self = cls()
        for fileName in cls.listdir(reader):
            if lazy:
                self._data[fileName] = _NOT_LOADED
            else:
                self._data[fileName] = cls.readf(reader, fileName)
        if lazy:
            self._reader = reader
        return self

    # MutableMapping methods

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, fileName):
        if self._data[fileName] is _NOT_LOADED:
            self._data[fileName] = self.__class__.readf(self._reader, fileName)
        return self._data[fileName]

    def __setitem__(self, fileName, data):
        # should we forbid overwrite?
        self._data[fileName] = data
        if fileName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(fileName)

    def __delitem__(self, fileName):
        del self._data[fileName]
        self._scheduledForDeletion.add(fileName)

    def __repr__(self):
        n = len(self._data)
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
        # Write data. Iterating over _data.items() prevents automatic loading.
        for fileName, data in self._data.items():
            # Two paths:
            # 1) We are saving in-place. Only write to disk what is loaded, it
            #    might be modified.
            # 2) We save elsewhere. Load all data files to write them back out.
            if data is _NOT_LOADED:
                if saveAs:
                    data = self.__class__.readf(self._reader, fileName)
                    self._data[fileName] = data
                else:
                    continue
            self.__class__.writef(writer, fileName, data)
        self._scheduledForDeletion = set()
        if saveAs:
            # all data was read by now, ref to reader no longer needed
            self._reader = None

    @property
    def fileNames(self):
        return list(self._data.keys())


class AttrDictMixin(Mapping):
    """ Read attribute values using mapping interface. For use with Anchors and
    Guidelines classes, where client code expects them to behave as dict.
    """

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __iter__(self):
        for key in attr.fields_dict(self.__class__):
            if getattr(self, key) is not None:
                yield key

    def __len__(self):
        return sum(1 for _ in self)
