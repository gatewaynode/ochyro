""" Ochyro
"""
from core import app, db
from core.models import Node, ContentType, User, Article


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Node": Node,
        "ContentType": ContentType,
        "User": User,
        "Article": Article,
    }
