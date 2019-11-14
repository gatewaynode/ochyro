from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from core import db
from core import login
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Node(db.Model):
    """The node model is the central organizing unit of the content model.
    
    This is pervasive, to the extent that almost everything a user interacts with in the site
    is content organized by at least one node, including the users themselves.  Nodes do not
    hold content themselves, but they reference content and the relationships of the content.
    Nodes may hold multiple content references, and content may even reference multiple other
    nodes, given the base constraint that nodes have only one immutable "first_child" and 
    content rows can only ever have one immutable "node_id" (these constraints are within the
    content system).
    """
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    hash = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user_history = db.Column(db.UnicodeText())
    tags = db.Column(db.UnicodeText(), index=True)
    first_child = db.Column(db.Integer, unique=True)
    _parents = db.Column(db.UnicodeText())
    parent_max_depth = db.Column(db.Integer)
    _children = db.Column(db.UnicodeText())
    child_max_depth = db.Column(db.Integer)
    next_node = db.Column(db.Integer)
    previous_node = db.Column(db.Integer)
    
    def __repr__(self):
        return {
            "id": self.id,
            "version": self.version,
            "first_child": self.first_child,
            "hash": self.hash,
            "timestamp": self.timestamp
        }


class NodeRevision(db.Model):
    """All content tables have related revision tables, all changes are saved as revisions.
    
    Content updates first save the existing content to it's appropriate revision table 
    including nodes themselves.  In this way the base tables are always the latest revision.
    """
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    hash = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user_history = db.Column(db.UnicodeText())
    tags = db.Column(db.UnicodeText(), index=True)
    first_child = db.Column(db.Integer, unique=True)
    _parents = db.Column(db.UnicodeText())
    parent_max_depth = db.Column(db.Integer)
    _children = db.Column(db.UnicodeText())
    child_max_depth = db.Column(db.Integer)
    next_node = db.Column(db.Integer)
    previous_node = db.Column(db.Integer)
    
    def __repr__(self):
        return {
            "id": self.id,
            "version": self.version,
            "first_child": self.first_child,
            "hash": self.hash,
            "timestamp": self.timestamp
        }


class User(UserMixin, db.Model):
    """User content type
    """
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    node_id = db.Column(db.Integer, index=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.Column(db.UnicodeText())

    def __repr__(self):
        return {
            "id": self.id,
            "node_id": self.node_id,
            "username": self.username
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserRevision(UserMixin, db.Model):
    """User revision table
    """
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    node_id = db.Column(db.Integer, index=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.Column(db.UnicodeText())

    def __repr__(self):
        return {
            "id": self.id,
            "node_id": self.node_id,
            "username": self.username
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Article(db.Model):
    """The most basic content type, a title field and a body field.
    
    The body field whitelists a small subset of HTML and filters out all other special 
    characters not required to support the HTML.
    """
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    node_id = db.Column(db.Integer, index=True)
    hash = db.Column(db.String(140))
    title = db.Column(db.String(200))
    body = db.Column(db.UnicodeText())
    
    def __repr__(self):
        return {
            "id": self.id,
            "content_version": self.content_version,
            "content_version": self.content_version,
            "node_id": self.node_id,
            "node_version": self.node_version,
            "hash": self.hash,
            "title": self.title
        }


class ArticleRevision(db.Model):
    """The article revisions table
    """
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    node_id = db.Column(db.Integer, index=True)
    hash = db.Column(db.String(140))
    title = db.Column(db.String(200))
    body = db.Column(db.UnicodeText())
    
    def __repr__(self):
        return {
            "id": self.id,
            "content_version": self.content_version,
            "node_id": self.node_id,
            "nove_version": self.node_version,
            "hash": self.hash,
            "title": self.title
        }
