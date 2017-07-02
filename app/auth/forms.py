from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    user_email = StringField('邮箱', validators=[DataRequired(), Length(max=64), Email()])
    user_password = PasswordField('密码', validators=[DataRequired(), Length(4, 64)])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登陆')


class RegistrationForm(FlaskForm):
    user_email = StringField('登陆邮箱', validators=[DataRequired(), Length(max=64), Email()])
    user_password = PasswordField('密码', validators=[DataRequired(),
                                                    Length(4, 64)])
    user_name = StringField('昵称', validators=[DataRequired(), Length(1, 64),
                                              Regexp(r'^[A-Za-z][\w_.]*$', 0,
                                                     '必须字母开头且只能包含字母数字或下划线_，点.')])
    submit = SubmitField('注册')

    def validate_user_email(self, field):
        if User.query.filter_by(user_email=field.data).first():
            raise ValidationError('邮箱已存在')

    def validate_user_name(self, field):
        if User.query.filter_by(user_name=field.data).first():
            raise ValidationError('昵称已存在~ 换一个吧')
