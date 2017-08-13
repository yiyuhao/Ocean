#!/usr/bin/env python
import os

# 从.env文件中导入环境变量
if os.path.exists('environment_var.env'):
    print('Importing environment from .env...')
    for line in open('environment_var.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]
    print('Imported env var')

from app import celery, create_app

app = create_app(os.getenv('OCEAN_ENVIRONMENT') or 'default')
app.app_context().push()
