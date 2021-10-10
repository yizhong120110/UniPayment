#!/bin/bash

LOGDIR=$LOGSDIR                                #log目录
sourcelogpath="${LOGDIR}/uwsgi.log"       #log源地址，与heuwsgi.xml.daemonize配置的文件一致
touchfile="${LOGDIR}/.touchforlogrotate"        #需要touch的文件(参考时间戳文件),与heuwsgi.xml.touch-logreopen配置的文件一致
DATE=`date -d "yesterday" +"%Y%m%d"`
destlogpath="${LOGDIR}/uwsgi.log.${DATE}" #重命名后的文件
mv $sourcelogpath $destlogpath
touch $touchfile                               #更新文件时间戳
