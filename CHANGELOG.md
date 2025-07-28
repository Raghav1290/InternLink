
# Change Log
All notable changes to the Login Example will be documented in this file.

Note that this log includes far more technical detail than would typically be
included in a change log. This project is intended to serve as a teaching tool,
and a resource for novice programmers. We understand you may have incorporated
parts of the code into your own projects. Therefore, it's important for this
log to cover internal code changes that would normally go undocumented.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [2.0.3] - 2025-02-24

This version removes the dependency on MySQL-Connector-Python, and introduces a
new dependency on the official "mysqlclient" project. This change is reflected
in requirements.txt, and the correct dependency will be installed if you're
setting up this project from scratch and creating a new virtual environment as
detailed in the [README](README.md).

You can also use the new db.py file from this version as a drop-in replacement
for the one provided with Login Example v2.0.2. If you're doing this, you will
need to:

    pip uninstall mysql-connector-python
    pip install mysqlclient

### Added

- Added this CHANGELOG file to track changes to the Login Example project.
- Added support for non-standard MySQL server ports. A port could previously be
  specified in [connect.py](loginapp/connect.py), but any port specified there
  was ignored and the default port (`3306`) was always used instead. The
  `init_db()` function in [db.py](loginapp/db.py) now provides an optional
  `port` parameter that can be used to specify a non-standard MySQL port if
  necessary. The updated [\_\_init\_\_.py](loginapp/__init__.py) file uses this
  new parameter to pass in the value of `dbport` in from connect.py. 

### Fixed

- Fixed database connectivity on Microsoft Windows 11 by modifying
  [db.py](loginapp/db.py) to use the unofficial
  [mysqlclient](https://pypi.org/project/mysqlclient/) package instead of
  [MySQL-Connector-Python](https://pypi.org/project/mysql-connector-python/).
  The mysqlclient version has been verified as working on Windows 10,
  Windows 11, and PythonAnywhere.
- Database port (`dbport`) is now correctly specified as an integer, rather
  than a string, in [connect.py](loginapp/connect.py).
- Fixed a logic error that would lead to an endless cycle of redirects if the
  user had a valid (i.e. correctly signed) login cookie that contained an
  invalid role name. This would never occur during 'normal' usage of the app,
  but could happen if role names were modified, added, or removed during
  development. This was addressed by modifying the `user_home_url()` function
  in [user.py](loginapp/user.py) to redirect users who have a valid login
  cookie, but an invalid role, to the `logout` endpoint. This removes their
  invalid session information, then forces them to log in again.