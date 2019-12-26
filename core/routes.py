from flask import render_template, flash, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required,
    login_manager,
)
from core import app, db, login
from core.forms import LoginForm, EditUserForm, EditArticleForm
from core.controllers import (
    normalize_form_input,
    save_user,
    save_article,
    load_node,
    load_content,
)

# from core.views import view_front_page, dictify_content, view_all, view_content_control
import core.views as views
from core.models import User
from werkzeug.urls import url_parse
from datetime import datetime
import html
import json
from pprint import pprint


@app.before_first_request
def setup_cms():
    if not len(User.query.all()):  # The implied short circuit
        import core.init_cms


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route("/")
@app.route("/index")
def index():
    articles = views.view_front_page()
    return render_template("index.html", title="", articles=articles)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()

    # @TODO Refactor this
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


@app.route("/edit/user", methods=["GET", "POST"])
@app.route("/edit/user/<node>", methods=["GET", "POST"])
@login_required
def edit_user(node=None):
    form = EditUserForm()
    if form.validate_on_submit():
        save_user(normalize_form_input(form))
        # current_user.username = form.username.data
        # db.session.commit()
        flash("User saved.")
        return redirect(url_for("index"))
    # elif request.method == "GET":
    #     form.username.data = current_user.username
    if node:
        content = load_content(load_node(node))
        # @TODO check locks here
        return render_template(
            "edit_user.html", title="Edit User", content=content, form=form
        )
    return render_template("edit_user.html", title="Create User", form=form)


@app.route("/view/user/<node>", methods=["GET"])
@login_required
def view_user(node):
    content = views.view_node(node)
    return render_template(
        "user.html", title=content["content"].username, content=content
    )


@app.route("/edit/article/", methods=["GET", "POST"])
@app.route("/edit/article/<node>", methods=["GET", "POST"])
@login_required
def edit_article(node=None):
    form = EditArticleForm()
    if form.validate_on_submit():
        save_article(normalize_form_input(form))
        flash("Article saved.")
        return redirect(url_for("index"))
    if node:  # Edit an existing article
        content = load_content(load_node(node))
        # @TODO check locks here
        return render_template(
            "edit_article.html", title="Edit Article", form=form, content=content,
        )
    else:
        return render_template(
            "edit_article.html", title="Create Article", form=form, content=None
        )


@app.route("/view/article/<node>")
def view_article(node):
    content = views.view_node(node)
    return render_template(
        "article.html", title=content["content"].title, content=content
    )


@app.route("/content-control")
@login_required
def content_control():
    content = views.view_content_control()
    pprint(content)
    return render_template("content-control.html", content=content)


@app.route("/debug", methods=["GET"])
@login_required
def debug_something():
    root_user = {
        "node_id": "",
        "node_version": "",
        "username": "root",
        "email": "none@none.com",
        "password": "dog",
    }
    created_root_user = controllers.save_user(root_user)
    return json.dumps(vars(created_root_user["content"]), indent=4)
