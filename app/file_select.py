from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required


class FileSelectForm(Form):
    SelectMe = BooleanField('', default = False)