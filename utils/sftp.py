# -*- coding: utf-8 -*-
import os, traceback, glob, optparse ,paramiko ,re ,time
from utils.log.logger import log as app_log
logger = app_log.log

"""为了执行时可以加参数"""
class OptionParser (optparse.OptionParser):
    def check_required (self, opt):
        option = self.get_option(opt)
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)

"""通过SFTP方式操作远端服务器目录"""
class SFTP:
    def __init__( self, ip, port, user, pwd, path='' ):
        """ 开启SFTP并进入指定目录 """
        self.con = paramiko.Transport( ( ip,port ) )
        self.con.connect( username = user , password = pwd )
        self.sftp = paramiko.SFTPClient.from_transport( self.con )
        self.path = path
        if path != '':
            self.sftp.chdir( path )
    
    def close( self ):
        """ 关闭SFTP """
        self.con.close()
    
    def changedir( self, path ):
        """ 更改当前目录 """
        self.path = path
        self.sftp.chdir( path )
        
    def _allFiles( self, search_path, pattern, pathsep=os.pathsep ):
        """ 查找指定目录下符合指定模式的所有文件,以列表形式返回
            @param search_path  查询目录列表
            @param pattern      文件名模式
            @param pathsep      目录分隔符
        """
        for path in search_path.split( pathsep ):
            for match in glob.glob( os.path.join(path, pattern) ):
                yield match
    
    def searchFileFromSFTP( self, pattern ):
        """ 在SFTP的指定目录下查找文件
            @param pattern  文件名模式
        """
        namelist = []
        for filename in self.sftp.listdir():
            t_rs = re.search( pattern.replace('?','.?').replace('*','.*') , filename )
            if t_rs:
                namelist.append( filename )
        return namelist
    
    def searchFileFromSFTPCheckTime( self, pattern  ,seconds = 0  ):
        """ 在SFTP的指定目录下查找文件
            @param pattern  文件名模式  # 这里有个问题，没有校验是不是文件夹
            @param seconds  要求最后生成时间间隔，单位秒
        """
        namelist = []
        fn_lst = self.sftp.listdir()
        fattr_lst = self.sftp.listdir_attr()
        for i in range(len(fn_lst)):
            t_rs = re.search( pattern.replace('?','.?').replace('*','.*') , fn_lst[i] )
            if t_rs:
                if ( (time.time() - fattr_lst[i].st_mtime) >= int( seconds ) ):
                    namelist.append( fn_lst[i] )
                else:
                    logger.info( '文件生成时间不足%s分'%(seconds/60) )
                    return namelist ##生成时间不足，返回文件
        return namelist
    
    def upload( self, fromdir, pattern ):
        """ 上传文件
            @param fromdir  本地文件目录
            @param pattern  文件名模式
        """
        if len( fromdir ) == 0 or fromdir[-1] != os.sep:
            fromdir += os.sep
        flist = self._allFiles( fromdir, pattern )
        i = 0
        for f in flist:
            i += 1
            try:
                name = f.split( os.sep )[-1]
                #print '正在上传:', name
                self.sftp.put( os.path.join(fromdir,name) , name )
            except:
                #print '上传文件[%s]错误!' % name
                return False
        
        if i == 0:
            raise RuntimeError( '没有查找到任何文件！' )
        
        return True
        
    def download( self, todir, pattern, isBin=False ):
        """ 下载文件.注意:文件名中带中文的下载不下来
            @param todir        下载到本地的目录
            @param pattern      文件名,可以使用通配符批量下载文件
            @param isBin        是否是二进制文件.是=True;否=False
        """
        # 若目录最后不是'\',则补充之
        if todir[-1] != os.sep:
            todir += os.sep
            
        flist = self.searchFileFromSFTP( pattern )
        if len( flist ) == 0:
            #print '未找到文件[%s]!' % pattern
            return False
        fn = [] # 将下载到本地的文件列表(带目录)
        
        for f in flist:
            fn.append( os.path.join(todir ,f) )
        
        # 循环下载每一个文件
        for i in range( len(fn) ):
            try:
                #print '正在下载文件:', flist[i]
                self.sftp.get( flist[i] , fn[i] )
            except:
                logger.exception("sftp.get异常[%s],[%s]"%(str(flist[i]) , str(fn[i])))
                #print '下载文件[%s]时出错!' % flist[i]
                return False
        return True
    
    def downloadAS( self ,todir ,remotename, localname ):
        """下载单个文件并重命名
            @param todir            下载到本地的目录
            @param remotename       文件名,只能是单个文件
            @param localname        本地文件名
        """
        # 若目录最后不是'\',则补充之
        if todir[-1] != os.sep:
            todir += os.sep
            
        flist = self.searchFileFromSFTP( remotename )
        if len( flist ) == 0:
            logger.warning('未找到文件!' )
            return False
        try:
            self.sftp.get( flist[-1] , os.path.join(todir ,localname) )
        except:
            logger.exception("downloadAS下载异常")
            return False
        return True
    
    def deleteFileFromSFTP( self, pattern ):
        """ 删除文件,注意:文件名不能为中文
            @param pattern  要删除的文件名,可以使用通配符批量删除文件
        """
        flist = self.searchFileFromSFTP( pattern )
        if len( flist ) == 0:
            #print '未找到文件[%s]!' % pattern
            return False
        for f in flist:
            try:
                #print '正在删除文件:', f
                self.sftp.remove( f )
            except:
                #print '删除文件[%s]时出错!' % f
                return False
        return True
    
    def renameFileFromSFTP( self, oldname, newname ):
        """ 重命名SFTP上的某个文件名
            @param oldname  原文件名
            @param newname  欲改成的文件名
        """
        try:
            #print '正在将文件[%s]改名为[%s]' % ( oldname, newname )
            self.sftp.rename( oldname, newname )
            return True
        except:
            #print '将文件[%s]改名为[%s]时出错!' % ( oldname, newname )
            return False

    
#=================================================================================================
if __name__ == '__main__':
    ip='46.17.189.233'##服务器地址
    port=22             ##服务器端口号
    user='sjdev'   ##登陆用户名
    pwd='sjdev'        ##登陆密码
    
    st = SFTP( ip ,port ,user ,pwd ,path = '' )
    # 变更目录
#    st.changedir( 'test' )    # 成功
#    st.changedir( '新建文件夹' )    #  失败
    # 上传
#    st.upload( r'D:\TMP' , '*.log.*' )   # 成功
    # 删除
#    st.deleteFileFromSFTP( '*.log.*' )  # 目前只能是删除指定文件名   通配符方式成功
    # 重命名
#    st.renameFileFromSFTP( 'back.log.20120606' , 'back.log.20120606_shhx' )   # 同级目录下改名   成功
#    st.renameFileFromSFTP( './test/back.log.20120606' , './test/back.log.20120606_shhx' )   # 其他目录下的同级更名  成功
#    st.renameFileFromSFTP( 'back.log.20120606' , './test/back.log.20120606_shhx' )    # 前后目录不一致  成功
#    st.renameFileFromSFTP( 'back.log.20120606' , './新建文件夹/back.log.20120606_shhx' )    # 不支持中文   失败
#    st.renameFileFromSFTP( './新建文件夹/back.log.20120606' , './新建文件夹/back.log.20120606_shhx' )    # 不支持中文   失败
    # 下载文件
#    st.download( r'D:' , 'b??k.log.*' )   # 目前只能是下载指定文件名的文件，不能设置是否是二进制方式   通配符方式成功
#    st.downloadAS( r'D:' ,'key.txt' ,'key_test.txt' )
#    print st.searchFileFromSFTPCheckTime( 'key.txt' , 10*60*60 )
    st.close()
