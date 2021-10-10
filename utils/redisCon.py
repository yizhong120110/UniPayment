# -*-coding:utf8-*-
import redis
from redlock import RedLock

CONSTR = dict( host = '192.168.10.206' , port = 6379 , password = 'redisfesb', db = 0 )
class RedisCon(object):
    def __init__(self):
        if not hasattr(RedisCon, 'pool'):
            RedisCon.getRedisCon()  
        # 创建redis连接
        #self.con = redis.StrictRedis(connection_pool=RedisCon.pool)
        self.con = redis.Redis(connection_pool=RedisCon.pool)
        # 创建锁
        self.lock = RedLock("distributed_lock",connection_details=[CONSTR])

    @staticmethod
    def getRedisCon():
        RedisCon.pool = redis.ConnectionPool( host=CONSTR['host'], password = CONSTR['password'], port=CONSTR['port'], db=CONSTR['db'] )
    """
    string类型 {'key':'value'} redis操作
    """
    def setRedis(self, key, value, time=None):
        # 设置有效期
        if time:
            res = self.con.setex(key, time, value)
        else:
            res = self.con.set(key, value)
            # 永久生效
            #self.con.persist(key)
        return res


    def set_str(self, key, value, time=None):
        """
           设置string型的值
        """
        try:
            if time:
                self.con.setex(key, value, time)
            else:
                self.con.set(key, value)
            return 0
        except:
            raise
            return -1

    def setnx(self,key,value):
        return self.con.setnx(k,value)
    
    def incrRedis(self,key):
        return self.con.incr(key)
        
    def getRedis(self, key):
        try:
            return self.con.get(key).decode()
        except:
            return ''
    
    def getSet(key,value):
        return self.con.getset(key,value)
        
    def delRedis(self, key):
        res = self.con.delete(key)
        return res

    """
    hash类型，{'name':{'key':'value'}} redis操作
    """
    def setHashRedis(self, name, key, value):
        res = self.con.hset(name, key, value)
        return res


    def getHashRedis(self, name, key=None):
        # 判断key是否为空，不为空，获取指定name内的某个key的value; 为空则获取name对应的所有value
        if key:
            res = self.con.hget(name, key)
        else:
            res = self.con.hgetall(name)
        return res


    def delHashRedis(self, name, key=None):
        if key:
            res = self.con.hdel(name, key)
        else:
            res = self.con.delete(name)
        return res

    # 获取锁
    def get_lock(self):
        return self.lock.acquire()

    # 释放锁
    def release_lock(self):
        self.lock.release()
if __name__ == '__main__':
    rdc = RedisCon()
    
    rlock = rdc.get_lock()
    print(rlock)
    import time
    time.sleep(10)
    rdc.release_lock()
