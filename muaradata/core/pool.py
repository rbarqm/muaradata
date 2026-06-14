class ConnectionPool:
    def __init__(self, factory):
        self.factory = factory
        self._conn = None

    def get(self):
        if self._conn is None or self._is_closed(self._conn):
            self._conn = self.factory()
        return self._conn

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _is_closed(self, conn):
        return getattr(conn, "closed", False)
