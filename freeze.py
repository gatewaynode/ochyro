from flask_frozen import Freezer
from ochyro import app, db
from core import models

freezer = Freezer(app)

@freezer.register_generator
def view_article():
    for article in models.Article.query.all():
        yield {"node": article._node_id}

if __name__ == "__main__":
    freezer.freeze()
