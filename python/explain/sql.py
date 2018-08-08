from abc import abstractmethod, ABCMeta


class SQLiteBacked(object):
    """An object that is represented by the contents of a SQLite database."""
    def __init__(self, database):
        self.database = database


class SQLiteRow(SQLiteBacked, dict):
    """An object that is represented by a single row in a database.

    Provides helper methods for accessing columns/attributes of the row.
    """
    _QUERY = 'SELECT {} FROM {} WHERE id=={}'

    def __init__(self, database, row):
        """Construct object given the database, table name, and row number."""
        super().__init__(database)
        # print(type(self), row)
        if not isinstance(row, int):
            raise TypeError('Row must be int. Got ' + repr(row))
        self.row = row
        self.refresh_row_cache()

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(*c) for c in self.items()))

    def refresh_row_cache(self):
        c = self.database.execute(
            self._QUERY.format('*', self.table(), self.row))
        result = [(k[0], v) for k, v in zip(c.description, c.fetchone())]
        """:type: List[Tuple[str, Any]]"""
        self.update(result)

    @classmethod
    @abstractmethod
    def table(cls):
        raise NotImplementedError


class SQLiteCacheRow(SQLiteRow, metaclass=ABCMeta):
    ROW_CACHE = {}

    @classmethod
    def from_cache(cls, database, row):
        # print('from cache', cls, row)
        key = (database, cls, row)
        try:
            return SQLiteCacheRow.ROW_CACHE[key]
        except KeyError:
            row = cls(database, row)
            SQLiteCacheRow.ROW_CACHE[key] = row
            # row.populate_cache()
            return row

    # def populate_cache(self):
    #     """Populates the cache if it has not already been filled."""
    #     pass
