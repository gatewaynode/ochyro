from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    IntegerField,
    PasswordField,
    BooleanField,
    SubmitField,
    HiddenField,
)
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
)
from core.models import User

# The regex r"^\w+$" accepts only alphanumerics and underscores


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Regexp(regex=r"^\w+$", message="Alphanumerics and underscores only."),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class EditUserForm(FlaskForm):
    username = StringField(
        "Username",
        description="Must be unique, underscores and alphanumerics only.",
        validators=[
            DataRequired(),
            Regexp(regex=r"^\w+$", message="Alphanumerics and underscores only."),
        ],
    )
    email = StringField(
        "Email",
        description="Valid email address required.",
        validators=[
            DataRequired(),
            Email(),
            Regexp(regex=r"^[\w.@+-\.]+$", message="Alphanumerics and '.@-' only."),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    node_id = HiddenField()
    node_version = HiddenField()
    node_hash = HiddenField()
    content_hash = HiddenField()
    content_type = HiddenField()
    submit = SubmitField("Save user")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                f"Username {username.data} already in use.  Please use a different username."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(
                f"Email {email.data} already in use.  Please us a different email address."
            )


class EditArticleForm(FlaskForm):
    title = StringField(
        "Title",
        description="HTML Allowed.",
        validators=[
            DataRequired(),
            Length(min=1, max=200, message="200 character max."),
        ],
    )
    body = TextAreaField(
        "Body",
        description="HTML Allowed.",
        validators=[
            DataRequired(),
            Length(min=1, message="Negative values not allowed."),
        ],
    )
    tags = TextAreaField(
        "Tags",
        description="Comma separated values, plaintext.",
        default="Untagged",
        validators=[DataRequired()],
    )
    node_id = HiddenField()
    node_version = HiddenField()
    node_hash = HiddenField()
    content_hash = HiddenField()
    content_type = HiddenField()
    submit = SubmitField("Save")
