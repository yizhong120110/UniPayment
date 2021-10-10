#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, io, time

CURRENT_USER = os.getlogin()
UWSGI_USER = CURRENT_USER  # Linux 上uwsgi代码所在的用户
NGINX_USER = CURRENT_USER  # Linux 上nginx代码所在的用户


def get_process(name, filter, user=None):
    #@param:name:进程名
    #@param:user:系统用户名
    if user:###针对多用户的情况，增加用户的查询
        cmd = 'ps -ef|grep ' + name + '|grep ' + user
    else:
        cmd = 'ps -ef|grep ' + name
        #print ('检测进程启动与否：%s'%( cmd ))
    r = os.popen(cmd)
    s = io.StringIO(r.read())
    pid = None
    for l in s:
        if filter(l):
            return filter(l)


def nginx(x):
    if 'nginx:' in x:
        d = x.split()
        if d[2] == '1':
            return d[1]
        else:
            return d[2]


def uwsgi(x):
    if 'wsgi.xml' in x:
        d = x.split()
        if d[2] == '1':
            return d[1]
        else:
            return d[2]


def start():
    print('启动 nginx ...')
    if get_process('nginx', nginx, user=NGINX_USER):
        print('nginx 已经启动')
    else:
        os.system(
            '%s/apps/nginx/sbin/nginx -c %s/apps/nginx/conf/nginx.conf' % (os.environ['HOME'], os.environ['HOME']))
        print('nginx 启动完毕')

    print('启动 web服务')
    if get_process('uwsgi', uwsgi, user=UWSGI_USER):
        print('web服务已经启动')
    else:
        os.system('uwsgi -x %s/src/ywt_flask/etc/uwsgi.xml' % (os.environ['HOME']))
        print('web服务 启动完毕')


def stop():
    pid = get_process('uwsgi', uwsgi, user=UWSGI_USER)
    if pid:
        print('uwsgi pid ' + pid)
        os.system('kill -9 ' + pid)
        print('web服务关闭成功')
    else:
        print('web服务未启动，不需关闭')


def stopall():
    stop()

    pid = get_process('nginx', nginx, user=NGINX_USER)
    if pid:
        print('nginx pid ' + pid)
        os.system('kill -15 ' + pid)
        print('nginx 关闭成功')
    else:
        print('nginx未启动，不需要关闭')


def restart():
    stop()
    time.sleep(2)
    start()


def restartall():
    stopall()
    time.sleep(2)
    start()

# 判断uwsgi是否启动，没有启动则重启一次
#*/2 * * * * /home/hxkh/src/backplat/crontab/runpy.sh ks.py isalive
# runpy.sh 应该有可执行权限
# 代码含义:每2分钟的时间间隔自动执行命令: ks.py isalive
def isalive():
    pid = get_process('uwsgi', uwsgi, user=UWSGI_USER)
    if pid:
        print('web服务已启动，不需要重启')
    else:
        print('web服务未启动，尝试重启')
        restart()


if __name__ == '__main__':
    import sys

    n = sys.argv[-1]
    if n.lower() == 'start':
        start()
    elif n.lower() == 'stop':
        stop()
    elif n.lower() == 'stopall':
        stopall()
    elif n.lower() == 'restart':
        restart()
    elif n.lower() == 'restartall':
        restartall()
    elif n.lower() == 'isalive':
        isalive()
    else:
        print('不支持该命令：', n)
