# -*- coding:utf8 -*-

from flask import Flask
from apps.views.uniplat import uniplat
from apps.views.general import general
from flask_apscheduler import APScheduler
from flask_cors import *

# 创建app
def create_app():
    app = Flask(__name__)
    # 设置配置文件
    #app.config.from_object('settings.DevelopmentConfig')
    # 如果使用下面的配置，则定时任务会找不到任务
    app.config.from_object('settings.DevelopmentConfig')

    # 支持跨域
    CORS(app, supports_credentials=True)  

    # 注册蓝图
    # 通用接口
    app.register_blueprint(general)
    # 统一收付接口
    app.register_blueprint(uniplat)

    # 注册schedule
    #scheduler = APScheduler()
    #scheduler.init_app(app)
    #scheduler.start()
    return app
