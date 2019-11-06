from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from core import app, db
from core.forms import LoginForm, RegistrationForm, EditProfileForm, EditArticleForm
from core.models import User
from werkzeug.urls import url_parse
from datetime import datetime
import html


@app.route("/")
@app.route("/index")
@login_required
def index():
    posts = [
        {
            "domain": "collegeboards.com",
            "dns_valid": True,
            "threat_score": 50
        },
        {
            "domain": "collegeboord.com",
            "dns_valid": True,
            "threat_score": 10
        },
        {
            "domain": "colegeboard.com",
            "dns_valid": True,
            "threat_score": 90
        }
    ]
    return(render_template("index.html", title="", posts=posts))


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
    if form.validate_on_submit():
        user = User(username=html.escape(form.username.data, quote=True), email=html.escape(form.email.data, quote=True))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congradulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="register", form=form)


@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    data = "some garbage data"
    return render_template("user.html", user=user, data=html.escape(data, quote=True))


@app.route("/edit/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
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
    return render_template("edit_article.html", title="Edit Article", form=form)
