from flask import flash
from core import db, login
from core.models import Node, NodeRevision, User, UserRevision, Article, ArticleRevision
from datetime import datetime

# from typing import Any
import hashlib
import traceback
import logging
import json

# import html


def _hash_table(db_object):
    """Hash the node with existing hash to form a Merkel chain (new nodes use an empty value here).

    Conditionals to handle the sqlalchemy object reference and timestamp being passed as an
    unhashable object.
    Parameters: node, an initialized db.model.Node
    Returns: a SHA256 hash digest
    """
    for attr, value in vars(db_object).items():  # Maybe change this to use __dict__ ?
        values_list = {}
        if not attr == "_sa_instance_state":
            if attr == "timestamp":
                values_list[attr] = str(value)
            else:
                values_list[attr] = value
    # Convert to JSON string, encode, get the sha256 hash and convert to standard output
    return hashlib.sha256(json.dumps(values_list).encode()).hexdigest()


def _register_node():
    """Create a node to register content to

    This creates an empty node that a piece of content can be attached to.
    """
    node = Node(version=1, timestamp=datetime.utcnow(), user_id=current_user.id,)
    db.session.add(node)
    db.session.commit()
    return node


def _associate_node(node, content):
    """Complete a node that was registered with a first_child association and hash
    """
    node.first_child = json.dumps(
        {
            "content_id": content.id,
            "content_revision": content.version,
            "content_type": "Article",
        }
    )
    node.hash = _hash_table(node)
    db.session.add(node)
    db.session.commit()

    return (node, content)


def node_load(node_id):
    """ Load a node table by id
    """
    try:
        safe_node_id = int(node_id)  # Typecast as a security measure
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(
            f"Security Warning: node_load({node_id}) failed to convert input to a integer!"
        )

    try:
        node = Node.query.get(safe_node_id)
    except Exception as e:
        logging.error(traceback.format_exc())

    # Load an object by string variable
    # obj = avail[name]()
    # or
    # module = __import__(module_name)
    # class_ = getattr(module, class_name)
    # instance = class_()

    return node


def content_load(content_id, ContentDbModel):
    """ Load a content row
    """
    try:
        safe_content_id = int(content_id)  # Typecast as a security measure
    except Exception as e:
        logging.error(traceback.format_exc())

    content = ContentDbModel.query.get(safe_content_id)

    return content


def save_revision(content, content_revision):
    content_revision.__dict__ = content.__dict__.copy()
    db.session.add(content_revision)
    db.session.commit()

    return content_revision


def register_user(form):
    user = User(
        username=html.escape(form.username.data, quote=True),
        email=html.escape(form.email.data, quote=True),
    )
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
    flash("Congradulations, you are now a registered user!")
    return f"Congradulations{html.escape(form.username.data, quote=True)}, you are now a registered user!"


def save_user(form):
    """Update a user

    Parameters: form, object.  A WTForms like object.
    """
    if form.node_id and form.node_version:
        node = node_load(form.form_id)

        if node.lock:
            locked = json.loads(node.lock)
            flash(
                f"This users node is locked by {locked['username']} since {locked['timestamp']}"
            )
            flash(f"User update not saved")
            return form

        existing_user = content_load(node.first_child, User)

        if existing_user.lock:
            locked = json.loads(existing_user.lock)
            flash(
                f"User profile is locked by {locked['username']} since {locked['timestamp']}"
            )
            flash(f"User update not saved")
            return form

        user_revision = save_revision(existing_user, UserRevision)

        new_version_number = user_revision.version + 1

        updated_user = User(
            id=user_revision.id,
            version=new_version_number,
            node_id=node.id,
            hash=user_revision.hash,
            lock="",  # This breaks any lock
            username=html.escape(form.username.data, quote=True),
            email=html.esscape(form.email.data, quote=True),
        )
        updated_user.set_password(form.password.data)
        updated_user.hash = _hash_table(updated_user)
        db.session.add(updated_user)
        db.session.commit()

        return (node, updated_user)

    else:  # Assume we are creating a new user
        node = _register_node()

        user = User(
            version=1,
            lock="",
            username=html.escape(form.username.data, quote=True),
            email=html.esscape(form.email.data, quote=True),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        user.hash = _hash_table(user)
        db.session.add(user)
        db.session.commit()

        data_pair = _associate_node(node, user)


def save_article(form):
    """Create or update an article content type

    Basic workflow:
    node create --> article create --> node assoicate to article --> node hash
    """
    if form.node_id and form.node_version:
        node = node_load(form.node_id)

        if node.lock:
            locked = json.loads(node.lock)
            flash(
                f"Node is locked by user{locked['username']} since {locked['timestamp']}"
            )
            flash(f"Edit not saved")
            return form

        existing_content = content_load(node.first_child, Article)

        if existing_content.lock:
            locked = json.loads(node.lock)
            flash(
                f"Content is locked by user{locked['username']} since {locked['timestamp']}"
            )
            flash(f"Edit not saved")
            return form

        content_revision = save_revision(existing_content, ArticleRevision)

        new_version_number = content_revision.version + 1

        updated_article = Article(
            version=new_version_number,
            node_id=node.id,
            hash=content_revision.hash,
            lock="",  # This breaks any lock
            title=form.title.data,  # @TODO add extra security measures
            body=form.body.data,  # @TODO add extra security measures
        )
        updated_article.hash = _hash_table(updated_article)
        db.session.add(updated_article)
        db.session.commit()

        return (node, updated_article)

    else:  # Assume new article
        node = _register_node()

        article = Article(version=1, lock="", title=form.title, body=form.body,)
        # First save get's our article ID to include in the hash
        db.session.add(article)
        db.session.commit()
        article.hash = _hash_table(article)
        db.session.add(article)
        db.session.commit()

        data_pair = _associate_node(node, article)

        return data_pair
