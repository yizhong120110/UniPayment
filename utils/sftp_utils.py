# -*- coding: utf-8 -*-
"""
    将stfp的文件上传、下载操作进行封装
"""
from .sftp import SFTP
from utils.utils import get_fesb_filename
from utils.log.logger import log as app_log
import os

logger = app_log.log


def sftp_put( host , port , user , passwd , path , filen ,localpath ):
    """
        把文件上传到服务器上
        参数列表：
            host:主机ip
            port:端口号
            user:用户名
            passwd:密码
            path:服务器端路径
            filen:文件名
            localpath:本地文件目录
        sftp_put("46.17.189.233" ,22 ,"sjdev" ,"sjdev" ,"/home/sjdev/tmp" ,"test.txt" ,get_fesb_filename('/'))
    """
    rs = False
    try:
        st = SFTP( host ,port ,user ,passwd ,path )
        # 上传
        rs = st.upload( localpath , filen )
        st.close()
    except:
        logger.exception("sftp_put上传异常") 
        return False
    return rs


def sftp_get( host , port , user , passwd , path , filen ,localpath ,localname ):
    """
        从服务器下载文件
        参数列表：
            host:主机ip
            port:端口号
            user:用户名
            passwd:密码
            path:服务器端路径
            filen:文件名
            localpath:本地文件目录
            localname:本地文件名称
        sftp_get("46.17.189.233" ,22 ,"sjdev" ,"sjdev" ,"/home/sjdev/tmp" ,"test.txt" ,get_fesb_filename('/tmp') ,"new.txt")
    """
    rs = False
    try:
        st = SFTP( host ,port ,user ,passwd ,path )
        # 下载
        os.makedirs(localpath , exist_ok = True)
        rs = st.downloadAS( localpath , filen ,localname )
        st.close()
    except:
        logger.exception("sftp_get下载异常") 
        return False
    return rs

def sftp_get_many( host , port , user , passwd , path , pattern ,localpath ):
    """
        从服务器下载文件
        参数列表：
            host:主机ip
            port:端口号
            user:用户名
            passwd:密码
            path:服务器端路径
            pattern:匹配文件模式
            localpath:本地文件目录
        sftp_get_many("172.18.1.152" ,22 ,"tcrp" ,"tcrp" ,"/home/tcrp/" ,"*.py" ,get_fesb_filename('/tmp'))
    """
    rs = False
    try:
        st = SFTP( host ,port ,user ,passwd ,path )
        # 下载
        os.makedirs(localpath , exist_ok = True)
        rs = st.download( localpath , pattern )
        st.close()
    except:
        logger.exception("sftp_get_many下载异常") 
        return False
    return rs


if __name__=="__main__":
    print(sftp_get("46.17.189.233" ,22 ,"sjdev" ,"sjdev" ,"/home/sjdev/tmp" ,"test.txt" ,get_fesb_filename('/tmp') ,"new.txt"))
