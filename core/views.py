from core import app, db
from core.models import Node, User, Article
from core.controllers import load_node, load_content
from pprint import pprint


def dictify_content(contents):
    content_dict = {}
    for content in contents:
        pprint(content)
        content_dict[content.__tablename__] = {}
        for attr, value in content.__dict__.items():
            if not attr == "_sa_instance_state":
                if attr == "timestamp" or attr == "_timestamp" or attr == "last_login":
                    content_dict[content.__tablename__][attr] = str(value)
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
