# -*- coding:utf8 -*-
#import time
import pymysql
from DBUtils.PooledDB import PooledDB,SharedDBConnection

POOL = PooledDB(
    creator = pymysql,          # 连接数据库的驱动
    maxconnections = 10,        # 连接池允许的最大连接数，0和None表示不限制连接数
    mincached = 2,              # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
    maxcached = 5,              # 链接池中最多闲置的链接，0和None不限制
    blocking = True,            # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
    maxusage = None,            # 一个连接最多被重复使用的次数，None表示无限制
    setsession = [],            # 开始会话前执行的命令列表
    ping = 0,                   # ping MySQL服务端，检查是否服务可用。0 = None = never
    host="192.168.1.205",
    port=3306,
    user="root",
    password="123456a?",
    database="paper",
    charset="utf8mb4"
)
