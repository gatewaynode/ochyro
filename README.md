Ochyro
======
**Entymology: (Greek), "fortress, stronghold, redoubt, block house"**

**Warning: under heavy development, not generally suitable for use**

A Content Management System that emphasizes security and ease of use.  Content model is graph based, not hierarchical.  Written in Python 3 built on Flask, Flask Migrate and SQL Alchemy, Tabulator and Ckeditor.  Primarily designed to build statically hosted web pages and provide headless content as JSON for single page and progressive apps.

Install
-------
Developed on Linux(KDE Neon).

Dependencies:
* Expects Python Invoke to already be installed (task runner)

`git clone git@github.com:gatewaynode/ochyro.git`

`cd ochyro`

`invoke virtualenv`

`source env/bin/activate`

`flask db init`

`flask db migrate`

`flask db upgrade`

`flask run`

Navigate to http://localhost:5000

Usage
-----
Simple article style content types are supported.  Sites are defined as a content type with an build function to create a static export in the site view page(barely working).

Road Map
--------
* REST Plus integration
* Graphene integration
* Workflows
* Multi-env, multi-site, multi-delivery platforms
* Config as code
* Plugin Framework
* Theming Framework
* Crypto caching

Contributions
-------------
Pull requests formatted with Black(strict PEP8 formatting) are welcome.
