SQLiteCookieJar
===============

An alternate [cookielib.FileCookieJar] that implements a SQLite storage for cookies. It is inspired by [RFC 6265] but not strictly compliant, since it sits on top of python's [cookielib].

SQLite storage model was inspired by Mozilla Firefox' cookies.sqlite.

Usage
-----

When instanciated without a `filename`, it places the file `python-cookies.sqlite` in the home directory of the user (e.g. `~/python-cookies.sqlite`).

```
    from sqlitecookiejar import SQLiteCookieJar
    
    jar = SQLiteCookieJar()     # the cookies will be stored in ~/python-cookies.sqlite
    jar.load()                  # load all the cookies from the file into the jar
    
    # Do stuff stuff with the cookies. You can eat them if you want.
    
    jar.save()                  # this will save all the cookies present in your jar
```

The module works like a charm with Kenneth Reitz' [requests].

```
    from sqlitecookiejar import SQLiteCookieJar
    from requests import Session
    
    path_to_jar = "/home/user/web/cookies/new_jar.sqlite"
    
    # set up a session with a brand new jar
    s = Session()
    s.cookies = SQLiteCookieJar(filename=path_to_jar)
    s.cookies.load()            # empty
    
    s.get("http://cookie-giving-url.com")   
    
    # now, you have cookies in your jar, you can save them
    s.cookies.save()
    
    
    jar = SQLiteCookieJar(filename=path_to_jar)
    jar.load()                  # contains the cookies given by cookie-giving-url.com
                                # could be reused in another session
```


Notes
-----
-   The nature of the file at `filename` is discovered automatically. If the given file is not a database or if the database doesn't match the standard format, the constructor will raise an exception.
-   This module is not compatible with the specific implementation of cookies in modern cookies, as the column names differ.
-   Expired cookies are flushed on every load.
-   This implementation won't save session cookies or expired cookies. Parameters `ignore_discard` and `ignore_expires` cannot be set to *True*. This is not fully compatible with Python's [cookielib.FilecookieJar] but rather follows RFC 6265, at least on this specific aspect.



  [cookielib.FilecookieJar]: https://docs.python.org/2/library/cookielib.html#cookielib.FileCookieJar
  [cookielib]: https://docs.python.org/2/library/cookielib.html
  [RFC 6265]: http://tools.ietf.org/html/rfc6265
  [requests]: http://docs.python-requests.org/en/latest/