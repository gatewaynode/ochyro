from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp
from core.models import User

# The regex r"^\w+$" accepts only alphanumerics and underscores

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Regexp(regex=r"^\w+$", message="Alphanumerics and underscores only.")])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Regexp(regex=r"^\w+$", message="Alphanumerics and underscores only.")])
    email = StringField("Email", validators=[DataRequired(), Email(), Regexp(regex=r"^[\w.@+-\.]+$", message="Alphanumerics and '.@-' only.")])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(f"Username {username.data} already in use.  Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(f"Email {email.data} already in use.  Please us a different email address.")


class EditUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Regexp(regex=r"^\w+$", message="Alphanumerics and underscores only.")])
    two_factor_auth = BooleanField("Enable 2FA")
    node_id = HiddenField()
    version_id = HiddenField()
    submit = SubmitField("Update Profile")


class EditArticleForm(FlaskForm):
    title = StringField("Title", description="HTML Allowed.", validators=[DataRequired(), Length(min=1, max=200, message="200 character max.")])
    body = TextAreaField("Body", description="HTML Allowed.", validators=[DataRequired(), Length(min=1, message="Negative values not allowed.")])
    tags = TextAreaField("Tags", description="Comma separated values, plaintext.", default="Untagged", validators=[DataRequired()])
    sticky = BooleanField("Sticky", description="Stick to top of lists.", default=False, validators=[DataRequired()])
    anchor = BooleanField("Anchor", description="Stick to bottom of lists.", default=False, validators=[DataRequired()])
    weight = IntegerField("Weight", description="Set's an arbitrary weight", default=0, validators=[DataRequired()])
    node_id = HiddenField()
    version_id = HiddenField()
    submit = SubmitField("Save")
