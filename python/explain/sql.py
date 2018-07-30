from sqlite3 import __init__


class SQLiteBacked(object):
    """An object that is represented by the contents of a SQLite database."""
    def __init__(self, database):
        self.database = database


class SQLiteRow(SQLiteBacked):
    """An object that is represented by a single row in a database.

    Provides helper methods for accessing columns/attributes of the row.
    """
    _QUERY = 'SELECT {} FROM {} WHERE id=={}'

    def __init__(self, database, table, row):
        """Construct object given the database, table name, and row number."""
        super().__init__(database)
        self.table = table
        if not isinstance(row, int):
            raise TypeError('Row primary key must be int. Got ' + repr(row))
        self.row = row

    def __getattr__(self, item):
        """If attribute is not found, fallback on database query for column."""
        try:
            return self.query1(item)
        except sqlite3.OperationalError:
            raise AttributeError(self.__class__.__name__ +
                                 ' has no attribute nor backing column ' +
                                 repr(item))

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(*c) for c in self.query('*')))

    def query(self, *columns):
        """Query columns from the row and return a list of column-value
        tuples."""
        cols = ', '.join(columns)
        c = self.database.execute(
            self._QUERY.format(cols, self.table, self.row))
        result = [(k[0], v) for k, v in zip(c.description, c.fetchone())]
        """:type: List[Tuple[str, Any]]"""
        return result

    def query1(self, column):
        """Query a single column and return only the value of the column."""
        return self.query(column)[0][1]