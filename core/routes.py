from flask import render_template, flash, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required,
    login_manager,
)
from core import app, db, login
from core.forms import LoginForm, RegistrationForm, EditUserForm, EditArticleForm
from core.controllers import save_user, save_article, load_node, load_content
from core.views import view_front_page, dictify_content, view_all
from core.models import User
from werkzeug.urls import url_parse
from datetime import datetime
import html
import json
from pprint import pprint


# Might need this down the road: https://flask-login.readthedocs.io/en/latest/
# But for now adding the get_id() class to the User model seems to have worked
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.filter_by(_id=int(user_id)).first()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route("/")
@app.route("/index")
def index():
    articles = view_front_page()
    return render_template("index.html", title="", articles=articles)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        current_user.last_login = datetime.utcnow()
        db.session.commit()

        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")

        return redirect(next_page)

    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    node = type("node", (object,), {})()
    if form.validate_on_submit():
        result = save_user(form)
        return redirect(url_for("login"))
    return render_template("register.html", title="register", form=form, node=node)


@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    data = "some garbage data"
    return render_template("user.html", user=user, data=html.escape(data, quote=True))


@app.route("/edit/user", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditUserForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@app.route("/edit/article", methods=["GET", "POST"])
@login_required
def edit_article():
    form = EditArticleForm()
    if form.validate_on_submit():
        save_article(form)
        return redirect(url_for("index"))
    return render_template("edit_article.html", title="Create Article", form=form)


@app.route("/edit/article/<node>/<version>", methods=["GET", "POST"])
@login_required
def edit_article_node(node=None, version=None):
    form = EditArticleForm()
    if form.validate_on_submit():
        save_article(form)
        return redirect(url_for("index"))
    if node and version:

        return render_template(
            "edit_article.html",
            title="Edit Article",
            form=form,
            node_id=node,
            node_version=version,
        )


@app.route("/article/<_id>")
@login_required
def view_article(_id):
    content = view_article_node(_id)
    return render_template("article.html", title=content[1].title, content=content)


@app.route("/debug", methods=["GET"])
@login_required
def debug_something():
    contents = view_all()
    for content in contents:
        pass
    return "Debugging"
