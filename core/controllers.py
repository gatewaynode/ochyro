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
        "hash": node.hash,
        "timestamp": node.timestamp,
        "user_id": node.user_id,
        "user_history": node.user_history,
        "tags": node.tags,
        "_parents": node.parents,
        "_children": node._children,
        "first_child": node.first_child,
        "next_node": node.next_node,
        "last_node": node.last_node,
        "sticky": node.sticky,
        "anchor": node.anchor,
        "weight": node.weight
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
            existing_node = Node.query.filter(Node.id == form.node_id, Node.version == form.version).first()
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
    else:
        node = Node(
            id=form.node_id,
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
    """Creat or update a user
    
    Parameters: form, object.  A WTForms like object.
    """
    pass


def register_user(form):


def save_article(form):
    pass
