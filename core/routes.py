from flask import render_template, flash, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required,
    login_manager,
)
from core import app, db, login
from core.forms import LoginForm, EditUserForm, EditArticleForm, EditSiteForm
from core.controllers import (
    normalize_form_input,
    save_user,
    save_article,
    load_node,
    load_content,
    load,
)

import core.views as views
from core.models import User
from werkzeug.urls import url_parse
from datetime import datetime
import html
import json
from pprint import pprint


@app.before_first_request
def setup_cms():
    """Check that the root user is set, if not set it and the content types."""
    if not User.query.all():  # The implied short circuit
        import core.init_cms


@login.user_loader
def load_user(id):
    """Directly accesses the user table. WARNING: To be deprecated"""
    return User.query.get(int(id))


@app.route("/")
@app.route("/index")
def index():
    """Route for the base URL"""
    articles = views.view_front_page()
    return render_template("index.html", title="", articles=articles)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login form, also includes registration link if reg is open."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()

    # @TODO Refactor this around content model
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
    """Just logout functionality"""
    logout_user()
    return redirect(url_for("index"))


# Content type routes


@app.route("/edit/user", methods=["GET", "POST"])
@app.route("/edit/user/<node>", methods=["GET", "POST"])
@login_required
def edit_user(node=None):
    """Edit or create a user as per the <node> overloading."""
    form = EditUserForm()
    if form.validate_on_submit():
        save_user(normalize_form_input(form))
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
    """View a user using generic view"""
    content = views.view_node(node)
    return render_template(
        "user.html", title=content["content"].username, content=content
    )


@app.route("/edit/article/", methods=["GET", "POST"])
@app.route("/edit/article/<node>", methods=["GET", "POST"])
@login_required
def edit_article(node=None):
    """Edit or create an article as per the <node> overloading."""
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
    """View a article using generic view"""
    content = views.view_node(node)
    return render_template(
        "article.html", title=content["content"].title, content=content
    )


@app.route("/edit/site/", methods=["GET", "POST"])
@app.route("/edit/site/<node>", methods=["GET", "POST"])
@login_required
def edit_site(node=None):
    form = EditSiteForm()
    index_choices = views.view_all_articles_as_node_options()
    form.index_content.choices = index_choices
    if form.validate_on_submit():
        save_site(normalize_form_input(form))
        flash("Site saved.")
        return redirect(url_for("index"))
    if node:
        content = load(node)
        return render_template(
            "edit_site.html", title="Edit Site", form=form, content=content,
        )
    else:
        print("Form to pass:")
        pprint(vars(form))
        return render_template(
            "edit_site.html", title="Create Site", form=form, content=None,
        )


@app.route("/view/site/<node>")
@login_required
def view_site(node=None):
    """View a site using a generic view and template"""
    content = views.view_node(node)
    return render_template("generic.html", content=content)


# Composed view routes


@app.route("/view/articles-list")
def view_articles_list():
    """View a list of all articles by title linked to article view"""
    table_content = views.view_all_articles()
    return render_template("view_all_articles.html", table_content=table_content)


@app.route("/content-control")
@login_required
def content_control():
    """Primary content control mechanism, heavily relies on Tabulator."""
    content = views.view_content_control()
    return render_template("content-control.html", content=content)


@app.route("/debug", methods=["GET"])
@login_required
def debug_something():
    """Currently a backdoor access method, can be anything needing a route and testing."""
    root_user = {
        "node_id": "",
        "node_version": "",
        "username": "root",
        "email": "none@none.com",
        "password": "dog",
    }
    created_root_user = controllers.save_user(root_user)
    return json.dumps(vars(created_root_user["content"]), indent=4)
