# coding=utf-8
"""
    SQLiteCookieJar
    ~~~~~~~~~~~~~~~

    An alternate `FileCookieJar` that implements a SQLite storage for
    cookies. Inspired by RFC 6265 but not strictly compliant, since it
    sits on top of `cookielib`.

    SQLite storage was inspired by Mozilla Firefox cookies.sqlite.
"""

from cookielib import FileCookieJar, Cookie
import os.path
import sqlite3
import time
import logging


class SQLiteCookieJar(FileCookieJar):
    """
    This class implements the cookielib.FileCookieJar using a file-based
    SQLite database. There is no centralized database holding the cookies
    for a given user, so it does not exactly work like a browser. However,
    the default CookieJar database file will be stored in the user's home
    folder.

    This implementation is loosely based on RFC6265, more specifically on
    section 5.3 ... however, for compatibility reasons with python2.7's
    `cookielib.Cookie`, the following cookie-attributes are ignored :

    -   max-age
    -   http-only

    :param str filename:    The complete path to the CookieJar.
                            Defaults to HOME_FOLDER/python-cookies.sqlite
    :param logger:          The logger used to log errors, infos, etc.
                            Defaults to a basic ERROR stdout logger.
    :type logger:           `logging.Logger`

    """

    def __init__(self, logger=None, *args, **kwargs):
        FileCookieJar.__init__(self, *args, **kwargs)

        if logger is None:
            self.logger = logging.getLogger(__name__)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            handler.setLevel(logging.WARNING)
            self.logger.addHandler(handler)
        else:
            self.logger = logger


        if self.filename is None:
            self.filename = os.path.join(os.path.expanduser("~"), "python-cookies.sqlite")
            self.logger.warning("No filename argument specified. Your cookie jar will be in %s", self.filename)

        self._check_and_create_table()

    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        """
        Implementation of the save method.

        :param filename: MUST be None. There is only one file per CookieJar.
        :param ignore_discard: MUST be False. Session cookies are not saved.
        :param ignore_expires: MUST be False. Expired cookies are evicted.
        """
        self._check_save_load_params(filename, ignore_discard, ignore_expires)

        for cookie in self:
            self._save_cookie(cookie)


    def _flush(self):
        """
        Internal method that flushes the database. Cookies that have expired
        will be deleted.

        Used before and after loading cookies from/to the database.
        """
        try:
            with sqlite3.connect(self.filename) as con:
                con.execute("DELETE FROM cookie WHERE expiry < ?", (time.time(),))
        except sqlite3.DatabaseError:
            self.logger.error("Could not flush expired cookies", exc_info=True)


    def _save_cookie(self, cookie):
        """
        Save a single cookie in the database. Follows the algorithm described
        in RFC6265 section 5.3 Storage Model ; specifically subpoint 11.

        Due to this implementation sitting on top of python's cookielib, we
        are not RFC6265-compliant.

        If a cookie exists, update it.

        Otherwise, create a new one.

        Exit if the cookie is not fresh.

        :param cookie: The cookie to save.
        """
        _now = time.time()
        if cookie is None or cookie.expires is None or cookie.expires < _now:
            return
        try:
            with sqlite3.connect(self.filename) as con:

                self.logger.info(
                    "SAVING cookie [domain: %s , name : %s, value: %s]" % (cookie.domain, cookie.name, cookie.value)
                )

                res = con.execute("SELECT id FROM cookie WHERE domain = ? AND name = ? AND path = ?",
                    (cookie.domain, cookie.name, cookie.path)).fetchone()

                if res is not None:
                    id = res[0]
                    con.execute("UPDATE cookie SET value = ?, secure = ?, expiry = ?, last_access = ? WHERE id=?",
                        (cookie.value, cookie.secure, cookie.expires, _now, id))

                else:

                    if cookie.path is None or cookie.path == "":
                        cookie.path = "/"

                    con.execute(
                        "INSERT INTO "
                            "cookie (domain,name,value, path, expiry, last_access, creation_time, secure) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            cookie.domain,
                            cookie.name,
                            cookie.value,
                            cookie.path,
                            cookie.expires,
                            _now,
                            _now,
                            cookie.secure
                        )
                    )
        except sqlite3.DatabaseError:
            self.logger.error(
                "Could not save cookie [domain: %s , name : %s, value: %s]" % (cookie.domain,
                                                                               cookie.name,
                                                                               cookie.value),
                exc_info=True
            )


    def load(self, filename=None, ignore_discard=False, ignore_expires=False):
        """
        Overriding the default load method.

        Please note that old cookies are flushed from the databaase through
        :meth:`_flush`.

        :param filename: MUST be None. There is only one file per CookieJar.
        :param ignore_discard: MUST be False. Session cookies are not saved.
        :param ignore_expires: MUST be False. Expired cookies are evicted.
        """
        self._check_save_load_params(filename, ignore_discard, ignore_expires)
        self._flush()
        self._really_load()


    def _really_load(self):
        """
        Implementation of the _really_load method. Basically, it just loads
        everything in the database, and maps it to cookies
        """
        try:
            with sqlite3.connect(self.filename) as con:
                res = con.execute("SELECT * from cookie").fetchall()

                for cookie in res:

                    initial_dot = cookie["domain"].startswith(".")
                    c = Cookie( 0, cookie["name"], cookie["value"],
                                None, False,
                                cookie["domain"], initial_dot, initial_dot,
                                cookie["path"], cookie["path"]!="/",
                                cookie["secure"],
                                cookie["expiry"],
                                False,
                                None,
                                None,
                                {}
                               )

                    self.logger.info(
                        "LOADED cookie [domain: %s , name : %s, value: %s]" % (c.domain, c.name, c.value)
                    )

                    if not c.is_expired(time.time()):
                        self.set_cookie(c)

        except sqlite3.DatabaseError:
            self.logger.error("Loading cookies failed : could not access database", exc_info=True)


    def _check_save_load_params(self, filename, ignore_discard, ignore_expires):
        """
        Internal method to make sure the parameters passed to save() and
        load() comply with RFC6265. Also makes sure there is only one file
        per CookieJar.

        :param filename: MUST be None. There is only one file per CookieJar.
        :param ignore_discard: MUST be False. Session cookies are not saved.
        :param ignore_expires: MUST be False. Expired cookies are evicted.
        """
        if filename is not None:
            raise NotImplementedError("There is only one file per jar.")

        if ignore_discard:
            raise NotImplementedError("This implementation respects RFC6265 in regard to "
                                      "session cookies. They cannot be stored.")

        if ignore_expires:
            raise NotImplementedError("This implementation respects RFC6265 in regard to "
                                      "cookie expiry. No expired cookie can be kept in "
                                      "the jar. That's unhealthy, anyway.")

    def _check_and_create_table(self):
        """
        Internal method to make sure the provided database has the correct
        format. There are four possibilities :

        1.  The database has no tables, in which case it is a new database
            and we will create the table `cookie`.
        2.  The database has one table, called `cookie`, in which case we
            make a select on it to make sure it has the right columns. If
            it doesn't, we raise an exception
        3.  The database has one table but the name is not `cookie`. It's
            the wrong database, raise an exception.
        4.  The database has more than one table. It's the wrong database,
            raise an exception.
            
        Note : If the file is not a database, sqlite3 will crash with and
        raise a DatabaseError.
        """
        try:
            with sqlite3.connect(self.filename) as con:
                res = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

                if len(res) == 0:
                    # Case #1
                    con.execute("CREATE TABLE IF NOT EXISTS cookie "
                                "(id INTEGER NOT NULL PRIMARY KEY,"
                                "domain TEXT NOT NULL,"
                                "name TEXT NOT NULL,"
                                "value TEXT,"
                                "path TEXT NOT NULL DEFAULT '/',"
                                "expiry INTEGER NOT NULL,"
                                "last_access INTEGER NOT NULL,"
                                "creation_time INTEGER NOT NULL,"
                                "secure INTEGER NOT NULL DEFAULT 0,"
                                "CONSTRAINT cookie_unique UNIQUE (name, domain, path))")
                elif len(res) == 1:
                    # Cases #2 and #3
                    table_name = res[0][0]

                    if table_name != "cookie":
                        # Case #3
                        raise AttributeError("The specified database has one table named '%s', but the tabled should be"
                                             " named 'cookie'. Please provide a valid database." % table_name)

                    else:
                        # Case #2
                        res = con.execute("PRAGMA table_info(cookie)").fetchall()
                        columns = set([element[1] for element in res])
                        expected_columns = {u'id', u'domain', u'name', u'value', u'path', u'expiry', u'last_access',
                                            u'creation_time', u'secure'}
                        if len(columns.difference(expected_columns)) > 0:
                            raise AttributeError("The specified database has a table named 'cookie', but the column "
                                                 "names do not match. Expected : %s with %s elements; got %s with %s "
                                                 "elements instead." %
                                                 (list(expected_columns),
                                                  len(expected_columns),
                                                  list(columns),
                                                  len(columns)))

                else:
                    # Case #4
                    raise AttributeError("The specified database has more than one table. "
                                         "Please provide a valid database.")

        except sqlite3.DatabaseError:
            self.logger.error("Sanity checks failed : could not access database", exc_info=True)