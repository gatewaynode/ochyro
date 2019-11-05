from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from app import login
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    #posts = db.relationship("Post", backref="author", lazy="dynamic")
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    roles = db.Column(db.String(128))


    def __repr__(self):
        return f"<user {self.username}>"


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# Need to deprecate this table, db_migrate didn't catch the type change on the body from varchar to UnicodeText
#class Post(db.Model):
    #id = db.Column(db.Integer, primary_key=True)
    #title = db.Column(db.String(140))
    #body = db.Column(db.UnicodeText())
    #timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    #def __repr__(self):
        #return f"<Post {self.body}>"

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, index=True)
    hash = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(200))
    body = db.Column(db.UnicodeText())
    tags = db.Column(db.UnicodeText(), index=True)
    parents = db.Column(db.UnicodeText())
    children = db.Column(db.UnicodeText())
    sticky = db.Column(db.Boolean())
    anchor = db.Column(db.Boolean())
    weight = db.Column(db.Integer)
    
    def __repr__(self):
        return f"<Article {self.body}>"
