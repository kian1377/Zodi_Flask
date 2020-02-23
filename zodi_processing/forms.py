from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_wtf.html5 import NumberInput
from wtforms import FloatField, IntegerField, SubmitField, BooleanField, PasswordField, StringField, SelectField
from wtforms.validators import Optional, DataRequired

class UploadZodiForm(FlaskForm):
    psfs_choice = SelectField('Choose PSF Types',
                              choices=[('os5','OS5'), ('cgi','CGI')])
    users_zodi_file = FileField('Upload Your Zodiacal Model:',
                                validators = [FileRequired()])
    cmr = FloatField('Enter the core-mask radius value in milliarcseconds:',
                     widget = NumberInput(min=0,max=200),
                     default = 0,
                     validators = [DataRequired()])
    thresh = FloatField('Enter the threshold value:',
                        widget = NumberInput(min=1),
                        default = None,
                        validators = [Optional()])
    submit = SubmitField('Upload and Process')

class LoginForm(FlaskForm):
    username = StringField('Username', 
                           validators = [DataRequired()])
    password = PasswordField('Password',
                             validators = [DataRequired()])
    submit = SubmitField('Login')
