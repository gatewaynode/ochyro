from core import app, db
from core.models import Node, User, Article
from core.controllers import load_node, load_content, dictify_content
import json
from pprint import pprint


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


def view_node(node):
    try:
        safe_id = int(node)
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(
            f"Security Warning: view_article({node}) failed to convert input to a integer!"
        )
    content = load_content(load_node(safe_id))

    return content


def view_article_node(node):
    try:
        safe_id = int(node)
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(
            f"Security Warning: view_article({node}) failed to convert input to a integer!"
        )
    article_content = load_content(load_node(safe_id))

    return article_content


def view_all():
    all_content = []
    nodes = Node.query.all()
    for node in nodes:
        all_content.append(dictify_content(load_content(node)))

    return all_content


def view_content_control():
    all_content = []
    nodes = Node.query.all()
    for node in nodes:
        all_content.append(load_content(node))

    table_content = []
    for content in all_content:
        if (
            content["content"]._hash != content["type"]._hash
            and content["type"].name == "Article Content Type"
        ):
            table_content.append(
                {
                    "title": content["content"].title,
                    "type": content["type"].name,
                    "body": content["content"].body,
                    "view": f"<a href=\"{content['type'].view_url}/{content['node']._id}\">view</a>",
                    "edit": f"<a href=\"{content['type'].edit_url}/{content['node']._id}\">edit</a>",
                }
            )

    return json.dumps(table_content)
