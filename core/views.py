from core import app, db
from core.models import Node, User, Article
from core.controllers import load_node, load_content
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
