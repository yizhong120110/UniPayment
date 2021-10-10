from . import db_pool
import pymysql
from contextlib import contextmanager

"""
    定义数据库的接口
    使用方式：with connection() as con:
                result = con.fetchone('select * from users where name=%s and pwd = %s',[name,pwd])
    注意：%s需要去掉引号，pymysql会自动加上
    
"""

class DBConnection(object):
    # 连接池
    pool = None

    def __init__(self):
        self.conn = DBConnection.getConn()
        self.cursor = self.conn.cursor()

    @staticmethod
    def getConn():
        """
            静态方法，从连接池中获取连接
        """
        if DBConnection.pool is None:
            _conn = db_pool.POOL.connection()
            return _conn

    def fetchone(self,sql,param = None):
        if param is None:
            count = self.cursor.execute(sql)
        else:
            count = self.cursor.execute(sql,param)
        if count > 0:
            result = self.cursor.fetchone()
        else:
            result = None

        return result

    def fetchall(self,sql,param = None):
        if param is None:
            count = self.cursor.execute(sql)
        else:
            count = self.cursor.execute(sql,param)
        if count > 0:
            result = self.cursor.fetchall()
        else:  
            result = None

        return result

    def fetchmany(self,sql,num,param = None):
        if param is None:
            count = self.cursor.execute(sql)
        else:
            count = self.cursor.execute(sql,param)
        if count > 0:
            result = self.cursor.fetchmany(num)
        else:  
            result = None

        return result

    def insertOne(self,sql,value):
        """
            @summary:向表中插入一条记录
            @param sql：insert sql,变量绑定方式 (%s,%s)
            @param value：要插入的记录数据 tuple/list
        """
        self.cursor.execute(sql,value)

    def insertMany(self,sql,values):
        """
            @summary:向表中插入多条记录
            @param sql：insert sql,变量绑定方式 (%s,%s)
            @param value：要插入的记录数据 tuple/list ((),(),) [[],[],]
            @return: count 受影响的行数
        """
        count = self.cursor.executemany(sql,values)

        return count

    def __query(self,sql,param = None):
        if param is None:
            count = self.cursor.execute(sql)
        else:
            count = self.cursor.execute(sql,param)

        return count

    def update(self,sql,param = None):
        """
            @summary: 更新数据
            @param sql：upd sql,变量绑定方式 (%s,%s)
            @param param tuple/list 变量替换
            @return: count 受影响的行数
        """
        return self.__query(sql,param)

    def delete(self,sql,param = None):
        """
            @summary: 删除数据
            @param sql：插入sql,变量绑定方式 (%s,%s)
            @param param tuple/list 变量替换
            @return: count 受影响的行数
        """
        return self.__query(sql,param)

    # begin、end、dispose用于非上下文管理器方式的事务开启、结束的处理
    #def begin(self):
    #    """
    #        @summary: 开启事务
    #    """
    #    self.conn.autocommit(0)

    #def end(self,option='commit'):
    #    """
    #        @summary: 结束事务
    #    """
    #    if option == 'commit':
    #        self.conn.commit()
    #    else:
    #        self.conn.rollback()

    #def dispose(self,isEnd = 1):
    #    """
    #        @summary: 释放连接池资源
    #    """
    #    if isEnd == 1:
    #        self.end('commit')
    #    else:
    #        self.end('rollback')
    #    self.cursor.close()
    #    self.conn.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        try:
            self.conn.rollback()
        except:
            pass # rollback的异常不予处理

    def close(self):
        self.cursor.close()
        self.conn.close()

    

@contextmanager
def connection():
    """
        使用上下文管理器来调用数据库连接api
        usage：with connection() as dbapi:
                   dbapi.fetchone(sql)
    """
    con = None
    try:
        con = DBConnection()
        yield con
        con.commit()
    except:
        print("rollback")
        if con:
            con.rollback()
        raise
    finally:
        print("close")
        if con:
            con.close()
