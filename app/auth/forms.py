from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    user_email = StringField('邮箱', validators=[DataRequired(), Length(max=64), Email()])
    user_password = PasswordField('密码', validators=[DataRequired(), Length(4, 64)])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登陆', render_kw={'style': 'width: 100%'})


class RegistrationForm(FlaskForm):
    user_email = StringField('登陆邮箱', validators=[DataRequired(), Length(max=64), Email()])
    user_password = PasswordField('密码', validators=[DataRequired(),
                                                    Length(4, 64)])
    user_name = StringField('昵称', validators=[DataRequired(), Length(1, 64),
                                              Regexp(r'^[A-Za-z][\w_.]*$', 0,
                                                     '必须字母开头且只能包含字母数字或下划线_，点.')])
    submit = SubmitField('注册', render_kw={'style': 'width: 100%'})

    def validate_user_email(self, field):
        if User.query.filter_by(user_email=field.data).first():
            raise ValidationError('邮箱已存在')

    def validate_user_name(self, field):
        if User.query.filter_by(user_name=field.data).first():
            raise ValidationError('昵称已存在~ 换一个吧')


class ChangeEmailForm(FlaskForm):
    new_user_email = StringField('新邮箱', validators=[Length(1, 64), DataRequired(), Email()])
    submit_email = SubmitField('保存', render_kw={'style': 'width: 100%'})

    def validate_new_user_email(self, field):
        if User.query.filter_by(user_email=field.data).first():
            raise ValidationError('邮箱已存在')


class GetBackPasswordForm(FlaskForm):
    user_email = StringField('请输入你的账户邮箱', validators=[Length(1, 64), DataRequired(), Email()])
    submit = SubmitField('确认', render_kw={'style': 'width: 100%'})


class PasswordResetForm(FlaskForm):
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(4, 64)])
    new_password_repeat = PasswordField('再次确认新密码', validators=[DataRequired(),
                                                               Length(4, 64),
                                                               EqualTo('new_password', '两次输入必须一致')])
    submit = SubmitField('保存', render_kw={'style': 'width: 100%'})


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired(), Length(4, 64)])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(4, 64)])
    new_password_repeat = PasswordField('再次确认新密码', validators=[DataRequired(),
                                                               Length(4, 64),
                                                               EqualTo('new_password', '两次输入必须一致')])
    submit_password = SubmitField('保存', render_kw={'style': 'width: 100%'})

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_old_password(self, field):
        if not self.user.verify_password(field.data):
            raise ValidationError('密码错误')

    def validate_new_password(self, field):
        if self.user.verify_password(field.data):
            raise ValidationError('新密码与旧密码相同')
