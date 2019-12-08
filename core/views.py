from core import app, db
from core.models import Node, User, Article
from core.controllers import load_node, load_content
import json
from pprint import pprint


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


# This is probably the wrong way to do it, should stay in the content API
def view_front_page():
    raw_content = Article.query.all()
    articles = []
    for content in raw_content:
        node = Node.query.get(content._id)
        articles.append(
            {
                "node": {
                    "_id": node._id,
                    "_version": node._version,
                    "_hash": node._hash,
                    "first_child": node.first_child,
                    "__parents": node.layer_parents,
                    "__children": node.layer_children,
                },
                "content": {
                    "_id": content._id,
                    "_version": content._version,
                    "_hash": content._hash,
                    "title": content.title,
                    "body": content.body,
                },
            }
        )
    return articles


def view_article_node(_id):
    try:
        safe_id = int(_id)
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(
            f"Security Warning: view_article({_id}) failed to convert input to a integer!"
        )
    article_content = Article.query.get(safe_id).first_or_404()
    node = load_node(article_content._node_id)

    return (node, article_content)


def view_all():
    all_content = []
    nodes = Node.query.all()
    pprint(nodes)
    for node in nodes:
        all_content.append(dictify_content(load_content(node)))

    pprint(all_content)

    return all_content
