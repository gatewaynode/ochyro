Ochyro
======
**Entymology: (Greek), "fortress, stronghold, redoubt, block house"**

**Warning: under heavy development, not generally suitable for use**

A Content Management System that emphasizes security and ease of use.  Written in Python 3 built on Flask, Flask Migrate, Flask Freeze and SQL Alchemy, Tabulator and Ckeditor.  Primarily designed to build statically hosted web pages and provide headless content for single page and progressive apps.

Install
-------
Dependencies:
* Expects Python Invoke to already be installed (task runner)

`git clone git@github.com:gatewaynode/ochyro.git`

`invoke virtualenv`

`source env/bin/activate`

`flask db init`

`flask db migrate`

`flask db upgrade`

`flask run`

Navigate to http://localhost:5000
