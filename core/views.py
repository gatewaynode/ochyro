from core import app, db
from core.models import Node, User, Article
from pprint import pprint


def view_front_page():
    raw_content = Article.query.all()
    # pprint(raw_content)
    articles = []
    for content in raw_content:
        # print(content._id)
        node = Node.query.get(content._id)
        pprint(vars(node))
        articles.append(
            {
                "node": {
                    "_id": node._id,
                    "_version": node._version,
                    "_hash": node._hash,
                    "first_child": node.first_child,
                    "__parents": node._Node__parents,
                    "__children": node._Node__children,
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


def view_article():
    pass
