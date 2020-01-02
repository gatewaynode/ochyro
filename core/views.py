from core import app, db
from core.models import Node, User, Article, Site
from core.controllers import load, load_node, load_content, dictify_content
import logging
import traceback
import json
from pprint import pprint


# This is probably the wrong way to do it, should stay in the content API
def view_front_page():
    raw_content = Article.query.all()
    articles = []
    for content in raw_content:
        articles.append(load(content._node_id))
    return articles


def view_node(node_id):
    """A generic method of safely loading a single piece of content"""
    try:
        safe_id = int(node_id)
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(
            f"Security Warning: view_article({node}) failed to convert input to a integer!"
        )
    content = load(node_id)

    return content


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


def view_site_control():
    raw_sites = Site.query.all()
    sites = list(load(site._node_id) for site in raw_sites)

    table_content = []
    for site in sites:
        table_content.append(
            {
                "site_name": site["content"].site_name,
                "edit_site": f"<a href=\"{site['type'].edit_url}/{site['node']._id}\">edit</a>",
                "last_published": "",
            }
        )


def view_all_articles():
    articles = Article.query.all()
    contents = []
    for article in articles:
        contents.append(load(article._node_id))
    table_content = []
    for content in contents:
        table_content.append(
            {
                "title": f"<a href=\"{content['type'].view_url}/{content['node']._id}\">{content['content'].title}</a>",
                "date": str(content["content"]._timestamp),
            }
        )

    return json.dumps(table_content)


def view_all_articles_as_node_options():
    """Dynamically load articles as options for a form"""
    raw_options = Article.query.all()
    index_content_options = []
    for option in raw_options:
        index_content_options.append((option._node_id, option.title))

    return index_content_options
