from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from core import db
from core import login
from flask_login import UserMixin


@login.user_loader
def load_user(id):
    return User.query.get(int(id))  # Typecast for security


"""Common fields for the content model denoted by leading underscore

These are denoted with a leading single underscore to differentiate from reserved names
in SQL Alchemy and to distinguish from unique fields."""
# ID is the pervasive primary key for all tables
db.Model._id = db.Column(db.Integer, primary_key=True, index=True)
# Everything is versioned, this combines to be a second primary key in revision tables
db.Model._version = db.Column(db.Integer, index=True)
# Everything has a node and this is it's ID (redundant for nodes themselves)
db.Model._node_id = db.Column(db.Integer, index=True)
# Every database row has a hash of it's serialized database object before final save
db.Model._hash = db.Column(db.String(140))
# Everything in the database is timestamped
db.Model._timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
# Everything in the database is potentially editable and therefore must be lockable
db.Model._lock = db.Column(db.UnicodeText())


class Node(db.Model):
    """The node model is the central organizing unit of the content model.

    This is pervasive, to the extent that almost everything a user interacts with in the site
    is content organized by at least one node, including the users themselves.  Nodes do not
    hold content themselves, but they reference content and the relationships of the content.
    Nodes may hold multiple content references, and content may even reference multiple other
    nodes, given the base constraint that nodes have only one immutable "first_child" and
    content rows can only ever have one immutable "node_id" (these constraints are within the
    content system).

    Potentially recursively nested fields are denoted with a leading double underscore.
    This is to attempt to make cleared when fields require recursion crontrols in views
    and controllers.
    """

    user_id = db.Column(db.Integer, db.ForeignKey("user._id"))
    tags = db.Column(db.UnicodeText(), index=True)
    first_child = db.Column(db.String(200), index=True)
    __parents = db.Column(db.UnicodeText())
    __children = db.Column(db.UnicodeText())
    __next_node = db.Column(db.Integer)
    __previous_node = db.Column(db.Integer)

    def __repr__(self):
        return {
            "id": self._id,
            "version": self._version,
            "first_child": self.first_child,
            "hash": self._hash,
            "timestamp": self._timestamp,
        }


class NodeRevision(db.Model):
    """All content tables have related revision tables, all changes are saved as revisions.

    Content updates first save the existing content to it's appropriate revision table
    including nodes themselves.  In this way the base tables are always the latest revision.
    """

    user_id = db.Column(db.Integer, db.ForeignKey("user._id"))
    tags = db.Column(db.UnicodeText(), index=True)
    first_child = db.Column(db.String(200), index=True)
    _version = db.Column(db.Integer, primary_key=True, index=True)  # Revision override
    __parents = db.Column(db.UnicodeText())
    __children = db.Column(db.UnicodeText())
    __next_node = db.Column(db.Integer)
    __previous_node = db.Column(db.Integer)

    def __repr__(self):
        return {
            "id": self.id,
            "version": self.version,
            "first_child": self.first_child,
            "hash": self.hash,
            "timestamp": self.timestamp,
        }


class ContentType(db.Model):
    """This table holds metadata necessary to save and render content types
    """

    database_table = db.Column(db.String(200), index=True)
    content_class = db.Column(db.String(200))
    # There will be more here for controllers and views but this gets us started


class User(UserMixin, db.Model):
    """User content type
    """

    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.Column(db.UnicodeText())

    def __repr__(self):
        return {"id": self._id, "node_id": self.node_id, "username": self.username}

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return int(self._id)


class UserRevision(UserMixin, db.Model):
    """User revision table
    """

    _version = db.Column(db.Integer, primary_key=True, index=True)  # Revision override
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.Column(db.UnicodeText())

    def __repr__(self):
        return {"id": self._id, "node_id": self.node_id, "username": self.username}

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Article(db.Model):
    """The most basic content type, a title field and a body field.

    The body field whitelists a small subset of HTML and filters out all other special
    characters not required to support the HTML.
    """

    title = db.Column(db.String(200))
    body = db.Column(db.UnicodeText())

    def __repr__(self):
        return {
            "id": self._id,
            "content_version": self.content_version,
            "node_id": self.node_id,
            "hash": self._hash,
            "title": self.title,
            "body": self.body,
        }


class ArticleRevision(db.Model):
    """The article revisions table
    """

    # Common fields
    _version = db.Column(db.Integer, primary_key=True, index=True)  # Revision override
    title = db.Column(db.String(200))
    body = db.Column(db.UnicodeText())

    def __repr__(self):
        return {
            "id": self.id,
            "content_version": self.content_version,
            "node_id": self.node_id,
            "hash": self._hash,
            "title": self.title,
            "body": self.body,
        }
