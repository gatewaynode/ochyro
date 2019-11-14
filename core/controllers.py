from core import db, login
from core.models import Node, User, Article
from datetime import datetime
import hashlib
import traceback
import logging
import json
#import html

def _hash_node(node):
    """Hash the node with existing hash to form a Merkel chain (new nodes use an empty value here).  Uglier serialization than pickle but safer.
    
    Parameters: node, an initialized db.model.Node
    Returns: a SHA256 hash digest
    """
    node_dict = {
        "id": node.node_id,
        "version": node.version,
        "hash": node.hash, # Including the previous hash if it exists provides a Merkel chain of authority
        "timestamp": node.timestamp,
        "user_id": node.user_id,
        "user_history": node.user_history,
        "tags": node.tags,
        "first_child": node.first_child,
        "_parents": node.parents,
        "parent_max_depth": node.parent_max_depth,
        "_children": node._children,
        "child_max_depth": node.child_max_depth,
        "next_node": node.next_node,
        "last_node": node.last_node,
    }
    node_string = json.dumps(node_dict).encode()
    return hashlib.sha256(node_string).hexdigest()

def _save_node(form, table_name):
    """Saves a node, updating or creating as necessary
    
    Parameters: form, object.  Similar to a WTForm submitted object
    Parameters: table_name, string.  Conforming to the flat content model of one unique table per content type.
    """
    if form.node_id and form.version:
        try:
            existing_node = Node.query.filter(
                Node.id == int(form.node_id), # Typecast to int as a security measure
                Node.version == int(form.version) # Typecast to int as a security measure
            ).first()
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error("Node id and version not found")
            return False
        
        if existing_node:
            node = Node(
                id=form.node_id,
                version=(form.version -= -1),
                hash=existing_node.hash,
                timestamp=datetime.utcnow(),
                user_id=current_user.id,
                user_history="",
                tags="",
                _parents="",
                _children="",
                first_child="",
                next_node="",
                last_node="",
                sticky="",
                anchor="",
                weight=""
            )
            node.hash = _hash_node(node)
            db.session.add(node)
            db.session.commit()
            return node
    else:
        # New node creation
        node = Node(
            version=1,
            hash="",
            timestamp=datetime.utcnow(),
            user_id="",
            user_history="",
            tags="",
            _parents="",
            _children="",
            first_child="",
            next_node="",
            last_node="",
            sticky="",
            anchor="",
            weight=""
        )
        node.hash = _hash_node(node)
        db.session.add(node)
        db.session.commit()
        return node

def edit_user():
    """Update a user
    
    Parameters: form, object.  A WTForms like object.
    """
    pass


def register_user(form):
    user = User(username=html.escape(form.username.data, quote=True), email=html.escape(form.email.data, quote=True))
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
    return f"Congradulations{html.escape(form.username.data, quote=True)}, you are now a registered user!"


def save_article(form):
    """Basic workflow  node create --> artucle create --> node assoicate to article --> node hash
    """
    pass
