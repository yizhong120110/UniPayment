# -*- coding:utf8 -*-
import os, logging

userhome = os.environ.get("HOME", "")


class BaseConfig(object):
    LOGDIR = os.path.join("%s", "src/paperyy/log") % (userhome)
    DEBUG = True
    LOGLEVEL = logging.DEBUG


class DevelopmentConfig(BaseConfig):
    ALIPAY_QRCODE_NOTIFY_URL = "http://abg85w.natappfree.cc/uniplat/callBack/ali"
    WECHAT_NOTIFY_URL = "http://j2ca97.natappfree.cc/uniplat/callBack/wechat"
    WECHAT_QRCODE_NOTIFY_URL = "http://j2ca97.natappfree.cc/uniplat/callBack/wechat/qrcode"
    WECHAT_JSAPI_NOTIFY_URL = "http://j2ca97.natappfree.cc/uniplat/callBack/wechat/jsapi"
    # 证书存储目录前缀
    KEY_CERT_PRE_PATH = r"D:\Work\12_Workspace_Python\UniPayment\keys"
    ALI_SANDBOX = True
    WECHAT_SANDBOX = True
    # 阿里云短信平台APPCODE
    ALIYUN_MESSAGE_URL = "https://smssend.shumaidata.com/sms/send"
    # 万维易源短信平台APPID
    SHOWAPI_APPID = "87178"
    # 万维易源短信平台APPSECRET
    SHOWAPI_SIGN = "c9cac5c2af75460e9474feee07e084bd"
    # 万维易源短信平台URL
    SHOWAPI_URL = "https://route.showapi.com/"
    # 万维易源短信平台模板ID
    SHOWAPI_TNUM = "T170317006214"
    # 定时任务调用开关
    SCHEDULER_API_ENABLED = True
    # 任务列表
    JOBS = [
        {
            'id': 'job',
            'func': 'task:balanceAlarm',
            'args': '',
            'trigger': 'interval',
            'seconds': 24 * 60 * 60,  # 24*60*60
        }
    ]

    # RMQ配置
    # MQS_CONNECTION_PARAMETER  = { 'host':'127.0.0.1' , 'port':5672 ,'user_name' : 'zsdev'  ,  'pass_word' : 'zsdev'  }
    # WQS_LOGIN = { 'exchange' : 'login' , 'exchange_type' : 'topic' }
    # WQS_ALIPAY = { 'exchange' : 'payment' , 'exchange_type' : 'topic' }
    # WQS_WXPAY = { 'exchange' : 'payment' , 'exchange_type' : 'topic' }



