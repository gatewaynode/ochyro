from flask import flash
from flask_login import current_user
from core import db, login
from core.models import Node, NodeRevision, User, UserRevision, Article, ArticleRevision
from datetime import datetime
import hashlib
import traceback
import logging
import json
import html
from pprint import pprint


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


# Sample Node lock{
#     "user_id": current_user.id,
#     "username": current_user.username,
#     "timestamp": str(datetime.utcnow()),
# }
def _check_node_lock(lock):
    if lock:
        locked = json.loads(lock)
        if locked["user_id"] == current_user._id:
            return False
        flash(
            f"This node has been locked by {locked['username']} since {locked['timestamp']}."
        )
        return True
    return False


def _check_content_lock(lock):
    if lock:
        locked = json.loads(lock)
        if locked["user_id"] == current_user._id:
            return False
        flash(
            f"This content has been locked by {locked['username']} since {locked['timestamp']}."
        )
        return True
    return False


def _register_node():
    """Create a node to register content to

    This creates an empty node that a piece of content can be attached to.
    """
    if current_user.is_authenticated:
        node = Node(_version=1, _timestamp=datetime.utcnow(), user_id=current_user._id)
    else:
        node = Node(_version=1, _timestamp=datetime.utcnow(), user_id=0)
    db.session.add(node)
    db.session.commit()
    return node


def _associate_node(node, content):
    """Complete a node that was registered with a first_child association and hash
    """
    node.first_child = json.dumps(
        {
            "content_id": content._id,
            "content_revision": content._version,
            "content_type": "Article",
        }
    )
    node._hash = _hash_table(node)
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
    pprint(vars(form))
    if form.node_id.data and form.node_version.data:  # Assume update
        node = node_load(form._node_id.data)
        if _check_node_lock(node._lock):
            return form

        existing_user = content_load(node.first_child, User)
        if _check_content_lock(existing_user._lock):
            return form

        user_revision = save_revision(existing_user, UserRevision)
        new_version_number = user_revision.version + 1
        updated_user = User(
            _id=user_revision._id,
            _version=new_version_number,
            _node_id=node._id,
            _hash=user_revision._hash,
            _lock="",
            username=html.escape(form.username.data, quote=True),
            email=html.escape(form.email.data, quote=True),
        )
        updated_user.set_password(form.password.data)
        updated_user.hash = _hash_table(updated_user)
        db.session.add(updated_user)
        db.session.commit()

        return (node, updated_user)

    else:  # Assume we are creating a new user
        node = _register_node()

        user = User(
            _version=1,
            _lock="",
            _node_id=node._id,
            username=html.escape(form.username.data, quote=True),
            email=html.escape(form.email.data, quote=True),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        user._hash = _hash_table(user)  # Now that we have the id we can hash
        db.session.add(user)
        db.session.commit()

        data_pair = _associate_node(node, user)


def save_article(form):
    """Create or update an article content type

    Basic workflow:
    node create --> article create --> node assoicate to article --> node hash
    """
    if form.node_id.data and form.node_version.data:  # Assume update
        node = node_load(form.node_id.data)
        if _check_node_lock(node._lock):
            return form

        existing_content = content_load(node.first_child, Article)
        if _check_content_lock(existing_content._lock):
            return form

        content_revision = save_revision(existing_content, ArticleRevision)
        new_version_number = content_revision.version + 1
        updated_article = Article(
            _version=new_version_number,
            _node_id=node._id,
            _hash=content_revision._hash,
            _lock="",
            title=form.title.data,  # @TODO add extra security measures
            body=form.body.data,  # @TODO add extra security measures
        )
        updated_article._hash = _hash_table(updated_article)
        db.session.add(updated_article)
        db.session.commit()

        return (node, updated_article)

    else:  # Assume new article
        node = _register_node()

        article = Article(version=1, _lock="", title=form.title, body=form.body,)
        # First save get's our article ID to include in the hash
        db.session.add(article)
        db.session.commit()
        article._hash = _hash_table(article)  # Hash after getting id
        db.session.add(article)
        db.session.commit()

        data_pair = _associate_node(node, article)

        return data_pair
