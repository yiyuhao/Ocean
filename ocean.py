from app import create_app
from flask_script import Manager
import os

app = create_app(os.getenv('OCEAN_ENVIRONMENT') or 'default')
manager = Manager(app)


@manager.command
def test():
    """单元测试"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    manager.run()
