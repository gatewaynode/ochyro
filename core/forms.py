from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    IntegerField,
    PasswordField,
    BooleanField,
    SubmitField,
    HiddenField,
    SelectField,
)
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    AnyOf,
)
from core.models import User

# The regex r"^\w+$" accepts only alphanumerics and underscores


class LoginForm(FlaskForm):
    """A simple login form.  WARNING: This will be deprecated"""

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
    """Create or edit users"""

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
    hidden_node_id = HiddenField()
    hidden_node_version = HiddenField()
    hidden_node_hash = HiddenField()
    hidden_content_hash = HiddenField()
    hidden_content_type = HiddenField()
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
    """Create or edit articles"""

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
    hidden_node_id = HiddenField()
    hidden_node_version = HiddenField()
    hidden_node_hash = HiddenField()
    hidden_content_hash = HiddenField()
    hidden_content_type = HiddenField()
    submit = SubmitField("Save")


class EditSiteForm(FlaskForm):
    """Create or edit site publishing endpoints"""

    site_name = StringField(
        "Site Name",
        description="A descriptive and unique name for the site",
        validators=[
            DataRequired(),
            Length(min=1, max=200, message="200 character max"),
        ],
    )
    local_build_dir = StringField(
        "Local Build Directory",
        description="The full local path to artifacts in",
        validators=[
            DataRequired(),
            Length(min=1, max=200, message="200 character max."),
        ],
    )
    static_files_dir = StringField(
        "Static Files Directory",
        description="The full local path to the static files directory for this site",
        validators=[
            DataRequired(),
            Length(min=1, max=200, message="200 character max"),
        ],
    )
    hosting_type_options = [(1, "Github Pages")]
    hosting_type = SelectField(
        "Hosting Type",
        description="The hosting type of the endpoint (only Github Pages currently supported)",
        coerce=int,
        choices=hosting_type_options,
        validators=[DataRequired()],
    )
    index_content = SelectField(
        "Content Index",
        description="The node ID for the front page index for the site",
        coerce=int,
        validators=[DataRequired()],
    )
    menu_content = TextAreaField()
    groups_content = TextAreaField()
    hidden_node_id = HiddenField()
    hidden_node_version = HiddenField()
    hidden_node_hash = HiddenField()
    hidden_content_hash = HiddenField()
    hidden_content_type = HiddenField()
    submit = SubmitField("Save")


class EditContentTypeForm(FlaskForm):
    name = StringField(
        "Content Type Name",
        description="An arbitrary name for the content type.",
        validators=[DataRequired()],
    )
    content_class = StringField(
        "Content Type Data Class",
        description="The SQL Alchemy database model class.",
        validators=[DataRequired()],
    )
    editable_fields = TextAreaField(
        "Editable Fields",
        description="Per field data on editable fields for filters, constraints, permissions in JSON format.",
        validators=[DataRequired()],
    )
    viewable_fields = TextAreaField(
        "Viewable Fields",
        description="Per field data on viewable fields for CSS classes, CSS IDs, validators, permissions, widgets in JSON format.",
        validators=[DataRequired()],
    )
    edit_url = StringField(
        "Edit URL",
        description="The generic URL for editing a content type.",
        validators=[DataRequired()],
    )
    view_url = StringField(
        "View URL",
        description="The generic URL for stand alone viewing of a content type.",
        validators=[DataRequired()],
    )
    hidden_node_id = HiddenField()
    hidden_node_version = HiddenField()
    hidden_node_hash = HiddenField()
    hidden_content_hash = HiddenField()
    hidden_content_type = HiddenField()
    submit = SubmitField("Save")
