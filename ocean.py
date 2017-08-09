from app import create_app, db
from app.models import User, Role, Post, Comment
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import os


COV = None
if os.environ.get('OCEAN_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

# 从.env文件中导入环境变量
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

app = create_app(os.getenv('OCEAN_ENVIRONMENT') or 'default')

manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Post=Post, Comment=Comment)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """单元测试"""
    if coverage and not os.environ.get('OCEAN_COVERAGE'):
        import sys
        os.environ['OCEAN_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('代码覆盖统计:')
        COV.report()
        base_dir = os.path.abspath(os.path.dirname(__file__))
        cov_dir = os.path.join(base_dir, 'tmp/coverage')
        COV.html_report(directory=cov_dir)
        print('HTML: file://{}/index.html'.format(cov_dir))
        COV.erase()


@manager.command
def deploy():
    from flask_migrate import upgrade
    from app.models import Role, User

    upgrade()

    Role.insert_roles()

    User.add_self_follows()


if __name__ == '__main__':
    manager.run()
