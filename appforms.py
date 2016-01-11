from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired


class ItemForm(Form):
    form_id = HiddenField(
        default="ItemForm",
        validators=[DataRequired()])
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', "images only"])])
    category = StringField('Category', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])


class ItemDeleteForm(Form):
    form_id = HiddenField(
        default="ItemDeleteForm",
        validators=[DataRequired()])


class LogoutForm(Form):
    form_id = HiddenField(
        default="LogoutForm",
        validators=[DataRequired()])
    state = StringField('state', validators=[DataRequired()])
