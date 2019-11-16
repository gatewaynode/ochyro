from core import db, login
from core.models import Node, User, Article
from datetime import datetime
from typing import Any
import hashlib
import traceback
import logging
import json
#import html

def _hash_table(db_object: Any) -> str:
    """Hash the node with existing hash to form a Merkel chain (new nodes use an empty value here).
    
    Conditionals to handle the sqlalchemy object reference and timestamp being passed as an 
    unhashable object.
    Parameters: node, an initialized db.model.Node
    Returns: a SHA256 hash digest
    """
    for attr, value in vars(db_object).items():
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
    node = Node(
        version=1,
        timestamp=datetime.utcnow(),
        user_id=current_user.id,
    )
    db.session.add(node)
    db.session.commit()
    return node


def _associate_node(node, content):
    """Complete a node that was registered with a first_child association and hash
    """
    node.first_child = content.id
    node.user_history = json.dumps([{
        "user_id": node.user_id,
        "node_version": node.version,
        "content_id": content.id,
        "content_version": content.version,
        "content_table": content.__table__,
        "timestamp": str(node.timestamp)
    }])
    node.hash = _hash_table(node)
    db.session.add(node)
    db.session.commit()
    
    return (node, content)


def node_load(node_id):
    """ Load a node table by id
    """
    try:
        safe_node_id = int(node_id) # Typecast as a security measure
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(f"Security Warning: node_load({node_id}) failed to convert input to a integer!")
    
    try:
        node = Node.query.get(safe_node_id)
    except Exception as e:
        logging.error(traceback.format_exc())
    
    return node


def content_load(content_id, ContentDbModel):
    """ Load a content row
    """
    try:
        safe_content_id = int(content_id) # Typecast as a security measure
    except Exception as e:
        logging.error(traceback.format_exc())
    
    content = ContentDbModel.query.get(safe_content_id)
    
    return content
    

def edit_user(form):
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
    """Create or update an article content type
    
    Basic workflow  node create --> artucle create --> node assoicate to article --> node hash
    """
    if form.node_id and form.node_version:
        node = node_load(form.node_id)
        
        content = content_load(node.first_child, Article)
        
        article = Article(
            version = 
        )
            
    else: # Assume new article
        node = _register_node()
        
        article = Article(
            version=1,
            lock = json.dumps({
                "user_id": current_user.id,
                "timestamp": str(datetime.utcnow())
            }),
            title = form.title,
            body = form.body
        )
        db.session.add(article)
        db.session.commit()
        article.hash = _hash_table(article)
        db.session.add(article)
        db.session.commit()
        
        thingy = _associate_node(node, article)
        
