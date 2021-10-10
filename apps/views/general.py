# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify,Response
from settings import DevelopmentConfig as DEVConfig
from utils.log.logger import log as app_log
from utils.pool.resultset import connection
from utils.utils import get_now
from urllib.parse import urlencode
from utils.httpRequestApi import ShowapiRequest
import requests,json
from utils.utils import getOrderNoByMysql,getOrderNoByRedis
#from utils.fdfs import FastDFSStorage
#from urllib.parse import urljoin
#import os,shutil,pika


"""
    可以加入一个功能准入验证，以uniplat_paybind为雏形
"""


devConfig = DEVConfig()
logger = app_log.log
general = Blueprint('general', __name__)

@general.route('/uniplat/general/genSeqNo',methods=['get'])
def genSeqNo():
    """
        为第三方站点生成自增序列号
        Mysql版本未在高并发环境下测试，如果在高并发环境下产生了重复的序列号，可切换至Redis版本
    """
    payChnl = request.args.get("payChnl")
    # 使用Mysql生成序列号
    orderNo = getOrderNoByMysql(payChnl)
    # 使用Redis生成序列号
    #orderNo = getOrderNoByRedis(payChnl)
    return orderNo



@general.route('/uniplat/general/sendMessage',methods=['post'])
def sendMessage():
    """
    短信发送接口
    阿里云平台没有模板管理功能，需要自己维护一个模板管理
    无参模板tag传空即可
    多参，参数项用|分隔
    """
    logger.info("发送短信")
    ret = {
        "head": {},
        "bizContent": {}
    }
    data = request.get_json(force=True)
    head = data.get("head")
    now = get_now("%Y%m%d %H%M%S")
    sDate, sTime = now.split(" ")
    head.update({
        "chnlDate": sDate,
        "chnlTime": sTime,
        "returnCode": "SUCCESS",
        "returnMessage": "业务受理成功"
    })
    try:
        # 调用方身份令牌
        chnlToken = head.get("chnlToken")
        # 调用方身份非空校验
        if not chnlToken:
            returnMessage = "参数项[chnlToken]不能为空"
            logger.debug(returnMessage)
            head.update({
                "returnCode": "FAIL",
                "returnMessage": returnMessage
            })
            ret.update({
                "head": head
            })
            return jsonify(ret)
        # 调用能力类别
        abilityType = head.get("abilityType")
        if not abilityType:
            returnMessage = "参数项[abilityType]不能为空"
            logger.debug(returnMessage)
            head.update({
                "returnCode": "FAIL",
                "returnMessage": returnMessage
            })
            ret.update({
                "head": head
            })
            return jsonify(ret)

        bizContent = data.get("bizContent")
        # 需要校验的报文体参数：
        bodyParams = ["templateNo", "phoneNo", "msgContent"]
        diff = list(set(bodyParams) - set(bizContent.keys()))
        for param in diff:
            returnMessage = f"参数项[{param}]不能为空"
            logger.debug(returnMessage)
            head.update({
                "returnCode": "FAIL",
                "returnMessage": returnMessage
            })
            ret.update({
                "head": head
            })
            return jsonify(ret)

        # 验证调用方能否调用本接口
        with connection() as con:
            sql = f"""select a.verified,a.token,b.app_id,coalesce(b.api_key,'') as api_key
                        from uniplat_ability_bind a,uniplat_ability_conf b
                            where a.token = '{chnlToken}'
                                and b.ability_type = '{abilityType}'
                                and a.relative_id = b.id"""
            logger.info(f"查询调用方信息：{sql}")
            row = con.fetchone(sql)
            if not row:
                returnMessage = "调用方不具备短信发送能力，请先申请"
                logger.info(returnMessage)
                head.update({
                    "returnCode": "FAIL",
                    "returnMessage": returnMessage
                })
                ret.update({
                    "head": head
                })
                return jsonify(ret)
            verified, token, appId, apiKey = row
            if verified != '1':
                returnMessage = "调用方短信发送能力未通过审核，请联系统一收付平台管理员"
                head.update({
                    "returnCode": "FAIL",
                    "returnMessage": returnMessage
                })
                ret.update({
                    "head": head
                })
                return jsonify(ret)
            # 调用方流水号
            chnlSeqNo = head.get("chnlSeqNo")
            templateNo = bizContent.get("templateNo")
            phoneNo = bizContent.get("phoneNo")
            msgContent = bizContent.get("msgContent")
            # 验证调用方流水号是否重复
            sql = f"select count(0) from uniplat_sms where chnl_seq_no = '{chnlSeqNo}'"
            logger.info(f"验证调用方流水号是否重复：{sql}")
            cnt = con.fetchone(sql)[0]
            if cnt != 0:
                returnMessage = "调用方流水号重复"
                head.update({
                    "returnCode": "FAIL",
                    "returnMessage": returnMessage
                })
                ret.update({
                    "head": head
                })
                return jsonify(ret)
        # 增加短信存储
        """
        {"msg":"成功","success":true,"code":200,"data":{"taskId":"st210106175352959abe782","orderNo":"946235647760466359"}}
        """
        queryParam = {
            "receive": phoneNo,
            "tag": msgContent,
            "templateId": templateNo
        }
        #url = urljoin(devConfig.SHOWAPI_URL, "28-1")
        sufix = urlencode(queryParam)
        url = devConfig.ALIYUN_MESSAGE_URL + "?" + sufix
        r = ShowapiRequest(url)
        r.addHeadPara("Authorization", "APPCODE " + appId)
        #r.addBodyPara("showapi_appid",appId)
        #r.addBodyPara("showapi_sign", apiKey)
        #r.addBodyPara("content", msgContent)
        #r.addBodyPara("mobile", phoneNo)
        #r.addBodyPara("tNum", templateNo)
        showapiRes = r.post()

        showapiRet = json.loads(showapiRes.text)
        logger.debug(showapiRet)
        showapiResCode = str(showapiRet.get("code", ""))
        showapiResMsg = showapiRet.get("msg", "")
        if showapiResCode == 200:
            taskId = showapiRet.get("data").get("taskID", "")
            status = "1"
        else:
            taskId = ""
            status = "0"

        bizContent = {
            "status": showapiResCode,
            "message": showapiResMsg
        }
        ret.update({
            "head": head,
            "bizContent": bizContent
        })
        with connection() as con:
            # 关于短信内容，此处仅存储进行变量替换的部分，完整的短信内容，可以将模板中de[]replace成{}，然后使用format(**kwargs)拼接出来
            sql = f"""insert into uniplat_sms(chnl_seq_no,taskid,phone,content,template,send_time,status,remark) 
                        values ("{chnlSeqNo}","{taskId}","{phoneNo}","{msgContent}","{templateNo}","{now}","{status}","{showapiResMsg}") """
            logger.debug(f"登记短信发送记录{sql}")
            con.insertOne(sql, [])
        return jsonify(ret)
    except Exception as e:
        logger.info("发送短信异常：%s" % e)
        head.update({
            "returnCode": "FAIL",
            "returnMessage": "发送短信异常"
        })
        ret.update({
            "head": head
        })
        return jsonify(ret)










