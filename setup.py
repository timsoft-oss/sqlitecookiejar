__author__ = 'dgarnier@timsoft.com'

from setuptools import setup

setup(
    name="sqlitecookiejar",
    description='FileCookieJar using SQLite files for persistence',
    py_modules=['sqlitecookiejar'],
    version='1.0.1',
    long_description=__doc__,
    zip_safe=False,
    author_email='dgarnier@timsoft.com',
    url='https://github.com/timsoft-oss/sqlitecookiejar',
    license='Apache 2.0',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Session'
    )
)