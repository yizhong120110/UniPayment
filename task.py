import requests,json
from utils.log.logger import log as app_log
from settings import DevelopmentConfig as DEVConfig
from utils.httpRequestApi import ShowapiRequest
from urllib.parse import urljoin

devConfig = DEVConfig()
logger = app_log.log

def balanceAlarm():
    logger.info( "定时任务启动，查询账户余额" )
    try:
        url = urljoin(devConfig.PAPERYY_URL, 'balance.aspx')
        appid = devConfig.APPID
        r = ShowapiRequest(url, appid)
        res = r.post()
        res = json.loads(res.text)
        ret = res.get('result')
        val = res.get('returnval')
        if ret != '1':
            logger.info(val)
            return
        else:
            if float(val) <= 100.00:
                logger.info("账户余额不足100元，发送短信提醒")
                res = sendMessage(devConfig.SHOWAPI_URL)
                logger.info(str(res))
    except Exception as e:
        logger.info( "查询账户余额异常，任务退出：%s"%e )
        return
    logger.info( "本次任务执行完成" )
    return

# 发送短信 限制条件:同一号码,30s不超过1条,10分钟不超过10条
def sendMessage(preUrl,funcNo = "28-1"):
    """
    :param mobile: 手机号码，必要
    :param content: string类型，使用json格式对应模板的键值对，动态内容使用,使用UTF-8编码强调下,json中的key和value如果不是数字,则必须用双引号包裹,不要用单引号，非必要
    :param tNum: 短信模板ID，必要
    :return ret_code：0为提交到队列成功，其他失败
    :return successCounts：计费长度
    :return remark：描述信息
    :return taskID：任务ID
    """
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2427.7 Safari/537.36"}
    body = {"showapi_appid":devConfig.SHOWAPI_APPID,
            "showapi_sign":devConfig.SHOWAPI_SIGN,
            "mobile":devConfig.PHONENO,
            "content":'{"amount":"%.2f"}'%devConfig.SHOWAPI_AMOUNT,
            "tNum":devConfig.SHOWAPI_TNUM
            }
    url = urljoin(preUrl, funcNo)
    res = requests.post(url, data=body, headers=headers)
    return json.loads(res.text)

if __name__ == "__main__":
    balanceAlarm()
