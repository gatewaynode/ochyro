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
    Site,
    SiteRevision,
)
from datetime import datetime
import hashlib
import traceback
import logging
import json
import base64
import html
import copy
from lxml.html.clean import clean_html
import re

# Crawl and build imports


from pprint import pprint


def normalize_form_input(form):
    """Take a WTF Form object and normalize as a flat dict."""
    normalized_data = {}
    for key, value in vars(form).items():
        if (
            not key.startswith("_")
            and key != "meta"
            and key != "submit"
            and not key.startswith("csrf")
        ):
            normalized_data[key] = value.data
    return normalized_data


# @TODO Trash this in favor of db.session.refresh(obj)
def _dictify_sqlalchemy_object(db_object):
    db_dict = dict(
        (value, getattr(db_object, value)) for value in db_object.__table__.columns
    )
    return db_dict


def _hash_table(db_object, chain=False):
    """Hashes an SQL Alchemy database object"""

    """NOTE: Make sure the object __dict__ is loaded, so after a db.session.commit() or a
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
    """Future state node locks to prevent changes during editing or long running query"""
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
    """Future state content locks for rows to prevent changes during operations."""
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
    """Create a simple node to register content to"""

    """This creates an empty node that a piece of content can be attached to.  All rows
    should have a corresponding node created first to be attached to.
    """
    if current_user.is_authenticated:
        node = Node(_version=1, _timestamp=datetime.utcnow(), user_id=current_user._id)
    else:
        node = Node(_version=1, _timestamp=datetime.utcnow(), user_id=0)
    db.session.add(node)
    db.session.commit()
    return node


def _associate_node(node, content, content_type):
    """Complete a node that was registered with a first_child association and hash"""

    """After content row creation link the row back to it's first parent node.
    Returns: full content dict."""
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

    return {"node": node, "content": content, "type": content_type}


def content_type_check_and_load(content_type_name):
    """Common function of saving content is to check and load the content type first"""

    content_type_content = ContentType.query.filter_by(
        name=content_type_name
    ).first()  # Filter sanity check, this is internal only input
    if not content_type_content:
        logging.error(f"Content Type '{content_type_name}' not found' crash and burn")
        exit(1)
    else:
        # Kind of redundant to load this again, but it sticks to the content model
        content_type = load(content_type_content._node_id)
        return content_type


def load_and_revise(node_id, content_revision_object):
    """Common function to save a revision of the existing content before updating"""

    existing_content = load(node_id)
    # @TODO Check hashes here just cause we can
    # @TODO Check locks here, if locked restore form and return user

    content_revision = save_revision(
        existing_content["content"], content_revision_object
    )
    return existing_content


def update_object_hash_and_save(existing_content, data):
    """Update the content object values filtering according to content type settings"""

    new_version_number = existing_content["content"]._version + 1

    # Set common update fields
    existing_content["content"]._version = new_version_number
    existing_content["content"]._lock = ""

    # Derive per field settings from content type unless this is a content type update
    if existing_content["content"]._hash != existing_content["type"]._hash:
        editable_fields = json.loads(existing_content["type"].editable_fields)

        already_set_values = ["_version", "_node_id", "_lock"]
        for key in data:
            print(key)
            # Security filter routines, not likely ever finalized
            if key not in already_set_values and not key.startswith("hidden_"):
                if editable_fields[key]["sec_filter_type"] == "REGEX":
                    # @TODO This is problematic, needs exception handling
                    regex = re.compile(editable_fields[key]["sec_filter_data"])
                    set_data = "".join(filter(regex.search, data[key]))
                elif editable_fields[key]["sec_filter_type"] == "PLAIN_TEXT":
                    # Strip everything but alphanumerics, spaces and some simple punctuation
                    regex = re.compile("[\w\?\!\,\_\-\.\s]")
                    set_data = "".join(filter(regex.search, data[key]))
                else:  # Assume None
                    set_data = data[key]

                setattr(existing_content["content"], key, set_data)

        db.session.add(existing_content["content"])
        db.session.commit()
        db.session.refresh(existing_content["content"])
        existing_content["content"]._hash = _hash_table(existing_content["content"])
        existing_content["content"]._hash_chain = _hash_table(
            existing_content["content"], chain=True
        )
        db.session.commit()
        db.session.refresh(existing_content["content"])

        return existing_content
    else:
        for key in data:
            setattr(existing_content["content"], key, data[key])
        db.session.add(existing_content["content"])
        db.session.commit()
        db.session.refresh(existing_content["content"])
        existing_content["content"]._hash = _hash_table(existing_content["content"])
        existing_content["content"]._hash_chain = _hash_table(
            existing_content["content"], chain=True
        )
        db.session.commit()
        db.session.refresh(existing_content["content"])


def load(node_id):
    """A simple wrapper for loading the node and then the first child"""
    node = load_node(node_id)
    content = load_content(node)
    return content


def load_node(node_id):
    """ Load a node table by id"""
    if node_id:
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
    """Given an node load it's first child content row and content type row"""

    """Returns the complete content dict which consists of three objects: the node, the
    content object, and the content type object."""
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
    """Given a a list of db objects that make up a piece of content, convert to dict"""

    """Within our simple content model this is reasonable to do as we can catch the objects
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
    """Always save a revision of any row that is updated or deleted."""
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


def save_user(data):
    """Create or update a user"""

    """Parameters: form, object.  A WTForms like object.
    """
    # Test content exists first
    content_type_content = ContentType.query.filter_by(name="User Content Type").first()

    if not content_type_content:
        error_out = json.dumps(data)
        logging.error(f"Content type not found or not loaded: data={error_out}")
        exit(1)
    else:
        # Kind of redundant to load this again, but it sticks to the content model
        content_type = load_content(load_node(content_type_content._node_id))

    if data["hidden_node_id"] and data["hidden_node_version"]:  # Assume update
        node = load_node(data["node_id"])
        if _check_node_lock(node._lock):
            return form

        existing_user = content_load(node)
        if _check_content_lock(existing_user._lock):
            return form

        user_revision = save_revision(existing_user, UserRevision)
        new_version_number = user_revision.version + 1
        existing_user["content"] = User(
            _version=new_version_number,
            _lock="",
            username=html.escape(data["username"], quote=True),
            email=html.escape(data["email"], quote=True),
        )
        if data["password"]:
            existing_user["content"].set_password(data["password"])
        existing_user["content"]._hash = _hash_table(existing_user["content"])
        existing_user["content"]._hash_chain = _hash_table(
            existing_user["content"], chain=True
        )
        existing_user["content"]._hash = _hash_table(
            article
        )  # Hash after updating object values
        existing_user["content"]._hash_chain = _hash_table(article, chain=True)
        db.session.add(existing_user["content"])
        db.session.commit()
        db.session.refresh(existing_user)

        return existing_user

    else:  # Assume we are creating a new user
        node = _register_node()

        user = User(
            _version=1,
            _lock="",
            _node_id=node._id,
            username=html.escape(data["username"], quote=True),
            email=html.escape(data["email"], quote=True),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        user._hash = _hash_table(user)  # Now that we have the id we can hash
        user._hash_chain = _hash_table(user, chain=True)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        content = _associate_node(node, user, content_type)

        return content


# Switch to normalized data from form objects to better work with REST and GraphQL later
def save_article(data):
    """Create or update an article content type"""

    """Basic workflow:
    node create --> article create --> node assoicate to article --> node hash
    """
    # Test content type exists first
    content_type_content = ContentType.query.filter_by(
        name="Article Content Type"
    ).first()
    if not content_type_content:
        logging.error("Content Type 'Article' not found' crash and burn")
        exit(1)
    else:
        # Kind of redundant to load this again, but it sticks to the content model
        content_type = load_content(load_node(content_type_content._node_id))

    if data["hidden_node_id"] and data["hidden_node_version"]:  # Assume update

        existing_content = load_content(load_node(data["hidden_node_id"]))
        # @TODO Check hashes here just cause we can
        # @TODO Check locks here, if locked restore form and return user

        content_revision = save_revision(existing_content["content"], ArticleRevision)

        new_version_number = existing_content["content"]._version + 1
        existing_content["content"]._version = new_version_number
        existing_content["content"]._node_id = existing_content["node"]._id
        existing_content["content"]._lock = ""
        existing_content["content"].title = clean_html(data["title"])
        existing_content["content"].body = clean_html(data["body"])
        existing_content["content"]._hash = _hash_table(existing_content["content"])
        existing_content["content"]._hash_chain = _hash_table(
            existing_content["content"], chain=True
        )
        existing_content["content"]._hash = _hash_table(
            existing_content["content"]
        )  # Hash after updating object values
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
            title=data["title"],
            body=data["body"],
        )
        # First save get's our article ID to include in the hash
        db.session.add(article)
        db.session.commit()
        db.session.refresh(article)
        article._hash = _hash_table(article)  # Hash after getting id
        article._hash_chain = _hash_table(article, chain=True)
        db.session.add(article)
        db.session.commit()
        db.session.refresh(article)

        content_obj = _associate_node(node, article, content_type)

        return content_obj


def save_site(data):
    """Create or update an site content type"""

    content_type = content_type_check_and_load("Site Content Type")

    if data["hidden_node_id"] and data["hidden_node_version"]:  # Assume update
        existing_content = load_and_revise(data["hidden_node_id"], SiteRevision)
        update_object_hash_and_save(existing_content, data)

        return existing_content

    else:  # Assume new site
        node = _register_node()

        site = Site(
            _version=1,
            _node_id=node._id,
            _lock="",
            site_name=data["site_name"],
            environment_name=data["environment_name"],
            local_build_dir=data["local_build_dir"],
            static_files_dir=data["static_files_dir"],
            hosting_type=data["hosting_type"],
            index_content=data["index_content"],
            menu_content=data["menu_content"],
            groups_content=data["groups_content"],
        )
        # First save get's our article ID to include in the hash
        #!!! <- being first save
        db.session.add(site)
        db.session.commit()
        db.session.refresh(site)
        #!!! -> end first saved
        ### reuse hash and save here
        site._hash = _hash_table(site)  # Hash after getting id
        site._hash_chain = _hash_table(site, chain=True)
        db.session.add(site)
        db.session.commit()
        db.session.refresh(site)

        content_obj = _associate_node(node, site, content_type)

        return content_obj


def save_content_type(data):
    """Update an content type (save currently disabled)"""

    content_type = "Content Type Content Type"  # Special exception

    if data["hidden_node_id"] and data["hidden_node_version"]:  # Assume update
        existing_content = load_and_revise(data["hidden_node_id"], ContentTypeRevision)

        update_object_hash_and_save(existing_content, data)

        return existing_content

    else:  # Assume new site
        # @TODO get to this later
        return False


# def build_static_site(data):
#     """Build a static site based on the site content type content"""
#     # Debugging
#     print('Build Static Site Function, "Data Received":')
#     pprint(data)
#     # Debugging
#
#     index_page = ""
#     if data["local_build_dir"] and os.path.isdir(
#         data["local_build_dir"]
#     ):  # validate the build dir exists
#         # wipe it and rebuild at this endpoint
#
#         try:
#             shutil.rmtree(data["local_build_dir"])
#         except Exception as e:
#             logging.error("There has been a problem removing the old site build.")
#             logging.error(traceback.format_exc())
#             return "Build Failed"
#
#     try:
#         os.makedirs(data["local_build_dir"])
#     except Exception as e:
#         logging.error(traceback.format_exc())
#         return "Build Failed"
#
#     try:
#         r = requests.get(
#             "http://localhost:5000"
#         )  # Cheating here, seems the index field needs to be more requests centric
#         index_page = r.text
#     except Exception as e:
#         logging.error(traceback.format_exc())
#         return "Build Failed"
#
#     try:
#         shutil.copytree(data["static_files_dir"], f"{data['local_build_dir']}/static")
#     except Exception as e:
#         logging.error(traceback.format_exc())
#         return "Build Failed"
#
#     try:
#         with open(f"{data['local_build_dir']}/index.html", "w") as file:
#             file.write(index_page)
#     except Exception as e:
#         logging.error(traceback.format_exc())
#         return "Build Failed"
#
#     # Spider links
#     if index_page:
#         soup = BeautifulSoup(index_page, "html.parser")
#         links = []
#         for link in soup.find_all("a"):
#             link_href = link.get("href")
#             if link_href.startswith("/") and link_href != "/index" and link_href != "/":
#                 print(link.get("href"))
#
#     return "Site build received"
