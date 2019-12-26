from core import db
from core import models, controllers
import json
import os
from pathlib import Path
from pprint import pprint

"""Create content types and root user before anything else."""


def init_content_type(build_content_type):
    """Separate from the normal controllers for now"""

    content_type_content = models.ContentType.query.filter_by(
        name=build_content_type["content_type_name"]
    ).first()
    if not content_type_content:
        node = controllers._register_node()

        content_type = models.ContentType(
            _version=1,
            _node_id=node._id,
            _hash="",
            _lock="",
            name=build_content_type["content_type_name"],
            content_class=build_content_type["content_class"],
            editable_fields=build_content_type["editable_fields"],
            viewable_fields=build_content_type["viewable_fields"],
            edit_url=build_content_type["edit_url"],
            view_url=build_content_type["view_url"],
        )
        db.session.add(content_type)
        db.session.commit()
        db.session.refresh(content_type)
        content_type._hash = controllers._hash_table(content_type)
        content_type._hash_chain = controllers._hash_table(content_type, chain=True)
        db.session.add(content_type)
        db.session.commit()

        db.session.refresh(node)
        node.first_child = json.dumps(
            {
                "content_id": content_type._id,
                "content_revision": content_type._version,
                "content_type_id": node._id,
                "content_type_name": build_content_type["content_type_name"],
                "content_type_class": build_content_type["content_class"],
            }
        )
        node._hash = controllers._hash_table(node)
        node._hash_chain = controllers._hash_table(node, chain=True)
        db.session.add(node)
        db.session.commit()

        return [node, content_type, content_type]
    else:
        print(
            f"Content type '{build_content_type['content_type_name']}' already exists"
        )
        return False


content_types = [
    {
        "content_type_name": "User Content Type",
        "content_class": "User",
        "editable_fields": "All",
        "viewable_fields": "All",
        "edit_url": "/edit/user",
        "view_url": "/view/user",
    },
    {
        "content_type_name": "Article Content Type",
        "content_class": "Article",
        "editable_fields": "All",
        "viewable_fields": "All",
        "edit_url": "/edit/article",
        "view_url": "/view/article",
    },
]

# Init step 1. Create the content types
if not models.ContentType.query.all():  # Sanity check
    for content_type in content_types:
        result = init_content_type(content_type)

# Init step 2. Create the root user
if not models.User.query.all():  # Sanity check
    root_user = {
        "node_id": "",
        "node_version": "",
        "username": "root",
        "email": "none@none.com",
        "password": "dog",
    }
    user_home = str(Path.home())
    with open(os.path.join(user_home, ".ochyro_root.txt"), "w") as file:
        file.write(json.dumps(root_user, indent=4))
    created_root_user = controllers.save_user(root_user)
