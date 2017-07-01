from app import create_app
from flask_script import Manager
import os

app = create_app(os.getenv('OCEAN_ENVIRONMENT') or 'default')
manager = Manager(app)

if __name__ == '__main__':
    manager.run()
