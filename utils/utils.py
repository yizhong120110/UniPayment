# -*- coding:utf8 -*-
import hashlib,os,time,datetime,zipfile
from utils.redisCon import RedisCon
from utils.log.logger import log as app_log
from settings import DevelopmentConfig as DEVConfig
from utils.pool.resultset import connection

logger = app_log.log
devConfig = DEVConfig()

def sha1(s,encoding = 'utf8'):
    return hashlib.sha1(s.encode(encoding)).hexdigest()

def get_fesb_filename(file_name):
    # 防止file_name的相对路径从“/”开始
    file_name = file_name.strip('/\\')
    return os.path.abspath(os.path.join(devConfig.RPC_FILE_ROOT, file_name))

# 获取毫秒级时间戳 20200109105627486
def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y%m%d%H%M%S", local_time)
    data_secs = (ct - int(ct)) * 1000
    time_stamp = "%s%03d" % (data_head, data_secs)
    return time_stamp

# md5加密
def cal_md5( obj, encoding='utf-8', isUpper = False ):
    """
    # 计算传入对象的md5值
    # 先将传入对象做str()处理，再计算
    """
    if isUpper:
        return hashlib.md5(str(obj).encode(encoding) ).hexdigest().upper()
    else:
        return hashlib.md5(str(obj).encode(encoding) ).hexdigest()

# 获取格式化的当前时间
def get_now( format = None ):
    if not format:
        return datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )
    else:
        return datetime.datetime.now().strftime( format )

# 日期相加
def sum_date( start,interval ):
    if not isinstance(start,str):
        raise "日期类型必须为字符串"
    try:
        startObj = datetime.datetime.strptime(start,'%Y-%m-%d %H:%M:%S')
        endObj = startObj + datetime.timedelta(int(interval))
        return endObj.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        return ''

# 使用mysql生成有序自增订单号
def getOrderNoByMysql( seqname ):
    """
        订单号生成规则：3位系统编码（暂定为UNP）+ 8位系统日期 + 6位系统时间 + 6位顺序号
        顺序号取自Mysql，会一直累加，不会每日清零
        如果需要每日清零的话，可以使用定时任务，每天凌晨重置tbl_sequence的值
    """
    logger.info(f"使用Mysql生成有序自增订单号|{seqname}")
    with connection() as con:
        sql = f"select count(0) from tbl_sequence where sequence_name = '{seqname}'"
        logger.info(sql)
        row = con.fetchone(sql)
        if not row:
            return ''
        else:
            sql = f"select next_val('{seqname}')"
            logger.info(sql)
            seqno = str(con.fetchone(sql)[0])
            dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            return ''.join( ['UNP',dt,f"{seqno:0>6}"] )

# 使用redis生成有序自增订单号
def getOrderNoByRedis( seqname ):
    logger.info(f"使用Redis生成有序自增订单号|{seqname}")
    rdc = RedisCon()
    seqno = rdc.incrRedis( seqname )
    # 首次请求这个序号组，设置过期时间为24小时 seq的类型为int
    if seqno == 1:
        logger.info( "首次请求序号组，设置过期时间" )
        rdc.setRedis( seqname,1,24*60*60 )
        #rdc.setRedis( seqname,1,60*10 )
    dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return ''.join( ['UNP',dt,f"{seqno:0>6}"] )

# 生成第三方论文查重系统token
def get_token( spam ):
    """
        spam：时间戳参数，自1970年1月1日以来持续的秒数
    """
    token_str = ''.join( (devConfig.NICK_ID,'$biyizhijia123456$',spam) )
    return cal_md5( token_str )

# 生成16位唯一码
import random
def createRandomString(len):
    raw = ""
    range1 = range(58, 65) # between 0~9 and A~Z
    range2 = range(91, 97) # between A~Z and a~z

    i = 0
    while i < len:
        seed = random.randint(48, 122)
        if ((seed in range1) or (seed in range2)):
            continue;
        raw += chr(seed);
        i += 1
    # print(raw)
    return raw

#def checkAbility(token: str,abilityType:str,con=None):
#    """
#    验证调用方权限
#    :param token:
#    :param abilityType:
#    :return:
#    """
#    with connection() as con:
#        sql = f"""select count(0) from uniplat_ability_bind a,uniplat_ability_conf b
#                    where a.token = '{token}
#                        and b.ability_type = '{abilityType}'
#                        and a.relative_id = b.id"""
#        cnt = con.fetchone(sql)[0]
#        if cnt != 0:
#            return True
#        else:
#            return False

def unzip(filename: str):
    try:
        file = zipfile.ZipFile(filename)
        dirname = filename.replace('.zip', '')
        # 如果存在与压缩包同名文件夹 提示信息并跳过
        if os.path.exists(dirname):
            print(f'{filename} dir has already existed')
            return ''
        else:
            # 创建文件夹，并解压
            os.mkdir(dirname)
            file.extractall(dirname)
            file.close()
            # 递归修复编码
            rename(dirname)
            return dirname
    except:
        print(f'{filename} unzip fail')
        return ''


def rename(pwd: str, filename=''):
    """压缩包内部文件有中文名, 解压后出现乱码，进行恢复"""

    path = f'{pwd}/{filename}'
    if os.path.isdir(path):
        for i in os.scandir(path):
            rename(path, i.name)
    newname = filename.encode('cp437').decode('gbk')
    os.rename(path, f'{pwd}/{newname}')


def getZipFile(filePath):
    """
        遍历文件目录，将所有文件按绝对路径存入列表中
        filPath:文件目录绝对路径
        return:搜索到的文件集合
    """
    fileList = []
    for root,dirs,files in os.walk(filePath):
        for file in files:
            fileList.append(os.path.join(root,file))
    return fileList

def zipFile(filePath, outputPath, outputName):
    """
        filePath：将要归档的目录绝对路径：D:\Work\12_Workspace_Python\paperyy\paper\report\PaperYY论文检测报告
        outputPath：生成的归档文件绝对路径：D:\Work\12_Workspace_Python\paperyy\paper\report
        outputName：生成的归档文件名：PaperYY论文检测报告.zip
    """
    dst = os.path.join(outputPath,outputName)
    newzip = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    fileList = getZipFile(filePath)
    for file in fileList:
        # 文件绝对路径：D:\Work\12_Workspace_Python\paperyy\paper\report\PaperYY论文检测报告\css\index.css
        fullFilePath = file
        # 归档的层级：按归档文件目录的相对路径归档至dst，而不是绝对路径
        # ['D:\Work\12_Workspace_Python\paperyy\paper\report\PaperYY论文检测报告\','css\index.css']
        compressedFilePath = file.split(filePath)[1]
        # be care full about these two parameters: full_file_path, compressed_file_path
        # as their names show.
        newzip.write(fullFilePath, compressedFilePath)
    newzip.close()
    return dst