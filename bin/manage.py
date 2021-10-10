# -*- coding:utf8 -*-
import path_init,os
from apps import create_app
from flask_script import Manager, Server
from flask_cors import CORS
from settings import DevelopmentConfig as DEVConfig
from utils.log.logger import log as app_log


devConfig = DEVConfig()
logger = app_log.log

# 创建flask app
app = create_app()


# 支持跨域,在生产环境下使用nginx支持跨域
#CORS(app, supports_credentials=True)
#CORS(app,resources=r'/*')

# 关于配置参数的使用：
#print(app.config.keys())
#print(app.config['SQLALCHEMY_DATABASE_URI'])

"""
# 自定义启动命令
    python manage.py runserver 
"""


manager = Manager(app)
manager.add_command("runserver", Server('192.168.1.35',port='9000'))

if __name__ == "__main__":
    manager.run()
