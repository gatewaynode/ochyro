from flask import flash
from flask_login import current_user
from core import db, login
from core.models import (
    Node,
    NodeRevision,
    ContentType,
    ContentTypeRevision,
    User,
    UserRevision,
    Article,
    ArticleRevision,
)
from datetime import datetime
import hashlib
import traceback
import logging
import json
import html
import copy
from pprint import pprint


# @TODO Trash this in favor of db.session.refresh(obj)
def _dictify_sqlalchemy_object(db_object):
    """Enumerates an sql alchemy object values even after commit (which flushes the dict)
    """
    db_dict = dict(
        (value, getattr(db_object, value)) for value in db_object.__table__.columns
    )
    return db_dict


def _hash_table(db_object, chain=False):
    """Hashes an SQL Alchemy database object

    NOTE: Make sure the object __dict__ is loaded, so after a db.session.commit() or a
    db.session.flush(), a db.session.refresh(db_object) is needed to populate the dict.

    By default this just hashes values that are not hashes themselves and are not SQL
    Alchemy instance state objects, by passing chain=True it will also hash existing
    hashes building a Merkel chain (if previous _hash_chain exists) which ensures we can
    check transactional integrity.

    Parameters: "db_object", an SQL Alchemy db object, "chain" boolean
    Returns: a SHA256 hash digest string
    """
    to_hash_dict = {}
    if chain:
        key_values_to_ignore = ["_sa_instance_state"]
    else:
        key_values_to_ignore = ["_sa_instance_state", "_hash", "_hash_chain"]
    for key, value in db_object.__dict__.items():
        if key not in key_values_to_ignore:
            if "datetime" in str(
                type(value)
            ):  # Convoluted but reliable way to spot datetime objects
                to_hash_dict[key] = str(value)
            else:
                to_hash_dict[key] = value
    return hashlib.sha256(json.dumps(to_hash_dict).encode()).hexdigest()


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


def _associate_node(node, content, content_type):
    """Complete a node that was registered with a first_child association and hash
    """
    db.session.refresh(node)
    node.first_child = json.dumps(
        {
            "content_id": content._id,
            "content_revision": content._version,
            "content_type_id": content_type["type"]._id,
        }
    )
    node._hash = _hash_table(node)
    node._hash_chain = _hash_table(node, chain=True)
    db.session.add(node)
    db.session.commit()

    return [node, content]


def load_node(node_id, node_version=None):
    """ Load a node table by id
    """
    if node_id and not node_version:
        try:
            safe_node_id = int(node_id)  # Typecast as a security measure
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(
                f"Security Warning: load_node({node_id}) failed to convert input to a integer!"
            )

        try:
            node = Node.query.get(safe_node_id)
            return node
        except Exception as e:
            logging.error(traceback.format_exc())
    else:
        pass


def load_content(node):
    """ Given an node load it's first child content row
    """
    first_child = json.loads(node.first_child)

    try:
        safe_content_id = int(
            first_child["content_id"]
        )  # Typecast as a security measure
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(
            f"Security Warning: load_content({node_id}) failed to convert input to a integer!"
        )

    content_type = ContentType.query.filter_by(
        _node_id=first_child["content_type_id"]
    ).first()
    if not content_type:
        return False

    # Check here if the content type _node_id matches the given node._id this signifies
    # a content type node and not a normal piece of content
    if node._id == content_type._node_id:
        return {
            "node": node,
            "content": content_type,
            "type": copy.deepcopy(content_type),
        }
    else:
        # Dynamically load the database model for the content type
        content_module = __import__(
            "core.models", fromlist=[content_type.content_class]
        )
        ContentClass = getattr(content_module, content_type.content_class)
        content = db.session.query(ContentClass).get(first_child["content_id"])

        return {"node": node, "content": content, "type": content_type}


def dictify_content(contents):
    """Given a a list of db objects that make up a piece of content, convert to dict

    Within our simple content model this is reasonable to do as we can catch the objects
    that won't convert to json and deal with them.
    """
    content_dict = {}
    for content in contents:
        content_dict[content.__tablename__] = {}
        for attr, value in content.__dict__.items():
            if not attr == "_sa_instance_state":
                # For timestamps get the string representation instead of the object
                if "datetime" in str(type(value)):
                    content_dict[content.__tablename__][attr] = str(value)
                # For values that are JSON documents import as native types
                elif (
                    "str" in str(type(value))
                    and value.startswith("[")
                    or "str" in str(type(value))
                    and value.startswith("{")
                ):
                    content_dict[content.__tablename__][attr] = json.loads(value)
                # Everything else just assign and store
                else:
                    content_dict[content.__tablename__][attr] = value
    return content_dict


def save_revision(content, content_revision_class):
    content_revision = content_revision_class(
        _id=content._id, _version=content._version
    )
    # Not the most graceful copy, but it seems to work
    for key, value in content.__dict__.items():
        if key != "_sa_instance_state":
            content_revision.__dict__[key] = value

    db.session.add(content_revision)
    db.session.commit()

    return content_revision


def save_user(form):
    """Update a user

    Parameters: form, object.  A WTForms like object.
    """
    # Test content exists first
    content_type_content = ContentType.query.filter_by(name="User Content Type").first()

    if not content_type_content:
        print("Houston we have a problem with the user content type.")
        exit(1)
    else:
        # Kind of redundant to load this again, but it sticks to the content model
        content_type = load_content(load_node(content_type_content._node_id))

    if form.node_id.data and form.node_version.data:  # Assume update
        node = load_node(form._node_id.data)
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
            _lock="",
            username=html.escape(form.username.data, quote=True),
            email=html.escape(form.email.data, quote=True),
        )
        updated_user.set_password(form.password.data)
        updated_user._hash = _hash_table(updated_user)
        updated_user._hash_chain = _hash_table(updated_user, chain=True)
        db.session.add(updated_user)
        db.session.commit()

        return [node, updated_user, content_type]

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
        db.session.refresh(user)
        user._hash = _hash_table(user)  # Now that we have the id we can hash
        user._hash_chain = _hash_table(user, chain=True)
        db.session.add(user)
        db.session.commit()

        data_pair = _associate_node(node, user, content_type)

        return data_pair


def save_article(form):
    """Create or update an article content type

    Basic workflow:
    node create --> article create --> node assoicate to article --> node hash
    """
    # Test content exists first
    content_type_content = ContentType.query.filter_by(
        name="Article Content Type"
    ).first()
    if not content_type_content:
        print("Houston we have a problem with the user content type.")
        exit(1)
    else:
        # Kind of redundant to load this again, but it sticks to the content model
        content_type = load_content(load_node(content_type_content._node_id))

    if form.node_id.data and form.node_version.data:  # Assume update

        existing_content = load_content(load_node(form.node_id.data))
        # @TODO Check hashes here just cause we can
        # @TODO Check locks here, if locked restore form and return user

        content_revision = save_revision(existing_content["content"], ArticleRevision)

        new_version_number = existing_content["content"]._version + 1
        existing_content["content"]._version = new_version_number
        existing_content["content"]._node_id = existing_content["node"]._id
        existing_content["content"]._lock = ""
        existing_content[
            "content"
        ].title = form.title.data  # @TODO add extra security measures
        existing_content[
            "content"
        ].body = form.body.data  # @TODO add extra security measures
        existing_content["content"]._hash = _hash_table(existing_content["content"])
        existing_content["content"]._hash_chain = _hash_table(
            existing_content["content"], chain=True
        )
        db.session.add(existing_content["content"])
        db.session.commit()
        db.session.refresh(existing_content["content"])

        return existing_content

    else:  # Assume new article
        node = _register_node()

        article = Article(
            _version=1,
            _node_id=node._id,
            _lock="",
            title=form.title.data,
            body=form.body.data,
        )
        # First save get's our article ID to include in the hash
        db.session.add(article)
        db.session.commit()
        db.session.refresh(article)
        article._hash = _hash_table(article)  # Hash after getting id
        article._hash_chain = _hash_table(article, chain=True)
        db.session.add(article)
        db.session.commit()

        data_pair = _associate_node(node, article, content_type)

        return data_pair
