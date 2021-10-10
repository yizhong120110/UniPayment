# -*- coding:utf8 -*-
import logging, os
from . import loghandler
from settings import DevelopmentConfig as DEVConfig

devConfig = DEVConfig()


def init_log(name=None, screen=False, thread=True):
    if name is None:
        name = ''
    screen = screen or devConfig.DEBUG
    if os.path.isdir(devConfig.LOGDIR) == False:
        os.makedirs(devConfig.LOGDIR)
    return init_logger(name, devConfig.LOGDIR, screen, thread)


init = init_log

# 将pika的日志级别调整为WARNING，其中包含pika.channel、pika.adapters.blocking_connection等等所有子name日志的级别
logging.getLogger("pika").setLevel(logging.WARNING)
# 将paramiko的日志级别调整为INFO
logging.getLogger("paramiko").setLevel(logging.INFO)


def init_logger(logname, logdir, screen=True, thread=True):
    logobj = logging.getLogger(logname)
    if logobj.handlers:
        return logobj

    # 初始化日志文件处理句柄
    # fn = logname
    # hdlr = loghandler.DateFileHandler(os.path.join(logdir, fn))
    # fmts = '%(asctime)s ' + ('T%(thread)d ' if thread else '') + '%(levelname)s %(message)s'
    # formatter = logging.Formatter(fmts)
    # hdlr.setFormatter(formatter)
    # logobj.addHandler(hdlr)

    if screen:
        # 初始化屏幕打印处理句柄
        hdlr = logging.StreamHandler()
        fmts = '%(asctime)s %(name)s：' + ('T%(thread)d ' if thread else '') + '%(filename)s ' + '%(lineno)d ' + '%(levelname)s %(message)s'
        formatter = logging.Formatter(fmts)
        hdlr.setFormatter(formatter)
        logobj.addHandler(hdlr)

    # logobj.setLevel(devConfig.LOGLEVEL)
    logobj.setLevel(logging.DEBUG)
    return logobj


class Logs(object):
    """
    直接使用的log
    """

    def __init__(self):
        self.log = init_log()


log = Logs()
