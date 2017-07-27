from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Regexp, ValidationError
from app.models import Role, User


class EditProfileForm(FlaskForm):
    user_about_me = TextAreaField('一句话介绍', validators=[Length(max=512)])
    user_location = StringField('所在城市', validators=[Length(max=64)])
    submit = SubmitField('保存')


class EditProfileAdminForm(FlaskForm):
    user_name = StringField('昵称', validators=[DataRequired(), Length(1, 64),
                                              Regexp(r'^[A-Za-z][\w_.]*$', 0,
                                                     '必须字母开头且只能包含字母数字或下划线_，点.')])
    user_email = StringField('登陆邮箱', validators=[Length(1, 64), DataRequired(), Email()])
    user_confirmed = BooleanField('标记为确认状态')
    role_id = SelectField('角色', coerce=int)
    user_about_me = TextAreaField('一句话介绍', validators=[Length(max=512)])
    user_location = StringField('所在城市', validators=[Length(max=64)])
    submit = SubmitField('确认修改[Admin]')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(role.role_id, role.role_name)
                                for role in Role.query.order_by(Role.role_name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.user_email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email已被注册')

    def validate_username(self, field):
        if field.data != self.user.user_username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('有重复昵称了')


class PostForm(FlaskForm):
    post_title = StringField('题目', validators=[DataRequired()])
    post_body = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('发表')


class EditPostForm(FlaskForm):
    post_title = StringField('题目', validators=[DataRequired()])
    post_body = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('修改')


class CommentForm(FlaskForm):
    comment_body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('评论')
