# -*- encoding: utf-8 -*-
'''
@File    :   bill.py    
@Contact :   yizhong120110@gmail.com
@Descrip :

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020/9/7 17:05   qiuy      1.0         None
'''
from settings import DevelopmentConfig as DEVConfig
from utils.log.logger import log as app_log
from utils.pool.resultset import connection
from alipay import AliPay
from alipay.exceptions import AliPayException
import os

devConfig = DEVConfig()
logger = app_log.log

def alipayBillQuery(**kwargs):
    try:
        #keyCertPath = r"D:\Work\12_Workspace_Python\UniPayment\keys\alipay\ndancy6417@sandbox.com"
        keyCertPath = r"D:\Work\12_Workspace_Python\UniPayment\keys\alipay\2021001107603998"
        # 读取应用私钥
        app_private_key_string = open(os.path.join(keyCertPath, 'app_private_key.pem')).read()
        # 读取支付宝公钥
        alipay_public_key_string = open(os.path.join(keyCertPath, 'ali_public_key.pem')).read()
        # 创建支付宝扫码支付对象
        alipay = AliPay(
            # 以下参数为沙箱测试的参数 正式              沙箱
            appid="2021001107603998",#2021001107603998  2016102000727260
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=False
        )
        # 获取账单下载地址
        bill = alipay.api_alipay_bill_downloadurl_query(
            bill_type="trade",
            bill_date="2020-08-11"
        )
        logger.debug(bill)
    except AliPayException as e:
        logger.info("调用alipay接口异常：%s" % e)
    except Exception as e:
        raise
        logger.info("下载支付宝账单异常：%s" % e)
    return ""

if __name__ == "__main__":
    alipayBillQuery()