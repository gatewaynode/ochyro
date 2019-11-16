""" Ochyro
"""
from core import app, db
from core.models import User, Article


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Article": Article}
