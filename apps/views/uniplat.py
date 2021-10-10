# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, Response
from settings import DevelopmentConfig as DEVConfig
from utils.log.logger import log as app_log
from utils.pool.resultset import connection
from utils.xmlparse import xml, xmlread
from utils.utils import get_now
import os, json, requests, datetime, pika
from alipay import AliPay
from alipay.exceptions import AliPayException
from wechatpy.pay import WeChatPay
from wechatpy.exceptions import WeChatPayException

devConfig = DEVConfig()
logger = app_log.log
uniplat = Blueprint('uniplat', __name__)


@uniplat.route('/uniplat/trade/test', methods=['get'])
def test():
    """
        服务有效性测试
    """
    logger.info("统一收付平台服务有效性测试")
    return "<h2>统一收付平台服务运行中 ...</h2>"


@uniplat.route('/uniplat/trade/payee', methods=['post'])
def payee():
    """
    第三方站点收款能力接口
    return:
    ret = {
        "head":{
            "returnCode": "UNP0000",
            "returnMessage": "Success"
        },
        "bizContent":{"status":"0"}

    }
    """
    logger.info("预创建支付订单")
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
        "chnlTime": sTime
    })
    try:
        bizContent = data.get("bizContent")
        # 调用方身份令牌
        chnlToken = head.get("chnlToken")
        # 调用能力类别
        abilityType = head.get("abilityType")
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
        # 调用能力类型非空校验
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

        # 需要校验的报文体参数：
        bodyParams = [ "totalPay", "subject"]
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


        # 支付类型为JSAPI时，需要上传openid，用户标识付款用户
        if abilityType in ("02","03"):
            # openid，微信公众号和小程序支付时需要上传openid，用于标识购买方
            openid = bizContent.get("openid", "")
            if not openid:
                returnMessage = "参数项[openid]不能为空"
                logger.debug(returnMessage)
                head.update({
                    "returnCode": "FAIL",
                    "returnMessage": returnMessage
                })
                ret.update({
                    "head": head
                })
                return jsonify(ret) 
        # 微信H5支付，需额外上传spbill_create_ip（终端IP）和scene_info（场景信息）参数
        if abilityType == "05":
            bodyParams = ["spbillCreateIp", "sceneType", "wapUrl","wapName"]
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
            sql = f"""select b.account,a.verified,a.token,b.app_id,coalesce(b.mch_id,'') as mch_id,coalesce(b.api_key,'') as api_key,b.key_cert_path 
                        from uniplat_ability_bind a,uniplat_ability_conf b
                            where a.token = '{chnlToken}'
                                and b.ability_type = '{abilityType}'
                                and a.relative_id = b.id"""
            logger.info(f"查询调用方信息：{sql}")
            row = con.fetchone(sql)
            if not row:
                returnMessage = "调用方不具备收款能力，请先申请"
                logger.info(returnMessage)
                head.update({
                    "returnCode": "FAIL",
                    "returnMessage": returnMessage
                })
                ret.update({
                    "head": head
                })
                return jsonify(ret)
            account, verified, token, appId, mchId, apiKey, keyCertPath = row
            logger.debug(keyCertPath)
            keyCertPath = os.path.join(devConfig.KEY_CERT_PRE_PATH,keyCertPath)
            logger.debug(keyCertPath)
            if verified != '1':
                returnMessage = "调用方收款能力未通过审核，请联系统一收付平台管理员"
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
            # 订单金额，单位：元
            totalPay = bizContent.get("totalPay")
            # 订单标题
            subject = bizContent.get("subject")
            # openid，微信公众号和小程序支付时需要上传openid
            openid = bizContent.get("openid", "")
            # 终端IP
            spbillCreateIp = bizContent.get("spbillCreateIp", "")
            # 场景信息-类型
            sceneType = bizContent.get("sceneType", "")
            # 场景信息-WAP url地址
            wapUrl = bizContent.get("wapUrl", "")
            # 场景信息-WAP网站名
            wapName = bizContent.get("wapName", "")
            # 支付结果返回页面URL
            returnUrl = bizContent.get("returnUrl", "")
            # 验证调用方流水号是否重复
            sql = f"select count(0) from uniplat_trans where chnl_seq_no = '{chnlSeqNo}'"
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
        if abilityType == '00':
            logger.info("支付宝当面付之扫码付款")
            aliRet = aliUniPay(
                abilityType=abilityType,
                account=account,
                totalPay=totalPay,
                chnlSeqNo=chnlSeqNo,
                token=token,
                appId=appId,
                keyCertPath=keyCertPath,
                subject=subject
            )
            head.update({
                "returnCode": "SUCCESS",
                "returnMessage": "业务已受理"
            })
            ret.update({
                "head": head,
                "bizContent": aliRet
            })
            logger.debug(ret)
            return jsonify(ret)
        elif abilityType == '01':
            logger.info("微信当面付之扫码付款")
            wechatRet = wechatUniPay(
                abilityType=abilityType,
                tradeType="NATIVE",
                account=account,
                totalPay=totalPay,
                chnlSeqNo=chnlSeqNo,
                token=token,
                appId=appId,
                mchId=mchId,
                apiKey=apiKey,
                subject=subject
            )
            head.update({
                "returnCode": "SUCCESS",
                "returnMessage": "业务已受理"
            })
            ret.update({
                "head": head,
                "bizContent": wechatRet
            })
            logger.debug(ret)
            return jsonify(ret)
        elif abilityType == '02':
            logger.info("微信公众号支付")
            wechatRet = wechatUniPay(
                abilityType=abilityType,
                tradeType="JSAPI",
                openId=openid,
                account=account,
                totalPay=totalPay,
                chnlSeqNo=chnlSeqNo,
                token=token,
                appId=appId,
                mchId=mchId,
                apiKey=apiKey,
                subject=subject
            )
            head.update({
                "returnCode": "SUCCESS",
                "returnMessage": "业务已受理"
            })
            ret.update({
                "head": head,
                "bizContent": wechatRet
            })
            logger.debug(ret)
            return jsonify(ret)
        elif abilityType == '03':
            logger.info("微信小程序支付")
            wechatRet = wechatUniPay(
                abilityType=abilityType,
                tradeType="JSAPI",
                openId=openid,
                account=account,
                totalPay=totalPay,
                chnlSeqNo=chnlSeqNo,
                token=token,
                appId=appId,
                mchId=mchId,
                apiKey=apiKey,
                subject=subject
            )
            head.update({
                "returnCode": "SUCCESS",
                "returnMessage": "业务已受理"
            })
            ret.update({
                "head": head,
                "bizContent": wechatRet
            })
            logger.debug(ret)
            return jsonify(ret)
        elif abilityType == '05':
            logger.info("微信H5支付")
            wechatRet = wechatUniPay(
                abilityType=abilityType,
                tradeType="MWEB",
                account=account,
                totalPay=totalPay,
                spbillCreateIp=spbillCreateIp,
                sceneType = sceneType,
                wapUrl = wapUrl,
                wapName = wapName,
                chnlSeqNo=chnlSeqNo,
                token=token,
                appId=appId,
                mchId=mchId,
                apiKey=apiKey,
                subject=subject
            )
            head.update({
                "returnCode": "SUCCESS",
                "returnMessage": "业务已受理"
            })
            ret.update({
                "head": head,
                "bizContent": wechatRet
            })
            logger.debug(ret)
            return jsonify(ret)
        elif abilityType == '06':
            logger.info("支付宝手机网站支付")
            aliRet = aliUniPay(
                abilityType=abilityType,
                account=account,
                totalPay=totalPay,
                chnlSeqNo=chnlSeqNo,
                token=token,
                appId=appId,
                keyCertPath=keyCertPath,
                returnUrl=returnUrl,
                subject=subject
            )
            head.update({
                "returnCode": "SUCCESS",
                "returnMessage": "业务已受理"
            })
            ret.update({
                "head": head,
                "bizContent": aliRet
            })
            logger.debug(ret)
            return jsonify(ret)
        else:
            returnMessage = "不支持此收款能力，请重新选择"
            logger.info(returnMessage)
            head.update({
                "returnCode": "FAIL",
                "returnMessage": returnMessage
            })
            ret.update({
                "head": head
            })
            return jsonify(ret)

    except Exception as e:
        logger.info("创建支付订单异常：%s" % e)
        head.update({
            "returnCode": "FAIL",
            "returnMessage": "创建支付订单异常"
        })
        ret.update({
            "head": head
        })
        return jsonify(ret)


def aliUniPay(**kwargs):
    """
    支付宝扫码付，向支付宝开放平台发送订单预创建请求，返回付款二维码链接
    由于同步通知和异步通知都可以作为支付完成的凭证，且异步通知支付宝一定会确保发送给商户服务端。
    为了简化集成流程，商户可以将同步结果仅仅作为一个支付结束的通知（忽略执行校验），实际支付是否成功，完全依赖服务端异步通知。
    """
    logger.info("支付宝统一收单线下交易预创建")
    abilityType = kwargs.get("abilityType")
    account = kwargs.get("account")
    totalPay = kwargs.get("totalPay")
    chnlSeqNo = kwargs.get("chnlSeqNo")
    token = kwargs.get("token")
    appId = kwargs.get("appId")
    keyCertPath = kwargs.get("keyCertPath")
    returnUrl = kwargs.get("returnUrl","")
    subject = kwargs.get("subject")
    ret = {"status": "10000", "message": "Success"}
    try:
        # 读取应用私钥
        app_private_key_string = open(os.path.join(keyCertPath, 'app_private_key.pem')).read()
        # 读取支付宝公钥
        alipay_public_key_string = open(os.path.join(keyCertPath, 'ali_public_key.pem')).read()
        # 创建支付宝扫码支付对象
        alipay = AliPay(
            # 以下参数为沙箱测试的参数
            appid=appId,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=devConfig.ALI_SANDBOX
        )
        # 扫码支付
        if abilityType == "00":
            qrorder = alipay.api_alipay_trade_precreate(
                # 订单编号
                out_trade_no=chnlSeqNo,
                # 订单金额
                total_amount=str(totalPay),
                # 商品描述
                subject=subject,
                # 异步通知URL
                notify_url=devConfig.ALIPAY_QRCODE_NOTIFY_URL
            )
            logger.debug(qrorder)
            status = qrorder.get("code")
            message = "|".join([qrorder.get("msg"), qrorder.get("sub_msg", "")])
        # 手机网站支付
        if abilityType == "06":
            order_string = alipay.api_alipay_trade_wap_pay(
                # 订单编号
                out_trade_no=chnlSeqNo,
                # 订单金额
                total_amount=str(totalPay),
                # 商品描述
                subject=subject
                # 支付结果返回URL
                return_url=devConfig.ALIPAY_RETURN_URL,
                # 异步通知URL
                notify_url=devConfig.ALIPAY_QRCODE_NOTIFY_URL
            )
            status = "10000"
        if status == "10000":
            # 接口调用成功，预登记支付订单
            now = get_now("%Y%m%d %H%M%S")
            sDate, sTime = now.split(" ")
            with connection() as con:
                transInfo = [chnlSeqNo, sDate, sTime, token, abilityType, account, totalPay, subject, "00"]
                sql = "insert into uniplat_trans(chnl_seq_no,chnl_date,chnl_time,token,trans_type,account,total_pay,subject,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                logger.info("预登记支付宝扫码付交易流水")
                cnt = con.insertOne(sql, transInfo)
            if abilityType == "00":
                codeUrl = qrorder.get("qr_code")
                ret.update({"codeUrl": codeUrl})
            if abilityType == "06":
                alipayUrl = devConfig.ALIPAY_GATEWAY + order_string
                ret.update({"alipayUrl": alipayUrl})
        else:
            logger.info(f"支付宝统一收单线下交易预创建失败 {status}:{message}")
            ret.update({"status": status, "message": message})
    except AliPayException as e:
        logger.info("调用alipay接口异常：%s" % e)
        ret.update({"status": e._AliPayException__code, "message": e._AliPayException__message})
    except Exception as e:
        logger.info("支付宝统一收单线下交易预创建异常：%s" % e)
        ret.update({"status": "90009", "message": "支付宝统一收单线下交易预创建异常"})
    return ret




def wechatUniPay(**kwargs):
    """
    微信支付，支持扫码付款、公众号付款
    扫码支付：NATIVE
    公众号支付：JSAPI
    小程序支付：JSAPI
    微信支付账户体系：https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=7_10&index=1

    """
    logger.info("微信付款统一下单交易创建")
    abilityType = kwargs.get("abilityType")
    # 交易类型 扫码付：NATIVE，公众号、小程序：JSAPI
    tradeType = kwargs.get("tradeType")
    logger.debug(tradeType)
    # 公众号和小程序支付时，通过微信客户端拉起支付，微信用户无需扫码直接付款，因此使用微信用户的openid作为买方的标识
    openId = kwargs.get("openId","")
    account = kwargs.get("account")
    # 商品金额
    totalPay = float(kwargs.get("totalPay"))
    # 商品金额 单位为分
    totalFee = int(totalPay * 100)
    chnlSeqNo = kwargs.get("chnlSeqNo")
    token = kwargs.get("token")
    appId = kwargs.get("appId")
    mchId = kwargs.get("mchId")
    apiKey = kwargs.get("apiKey")
    # 商品描述
    subject = kwargs.get("subject")
    spbillCreateIp = kwargs.get("spbillCreateIp")
    sceneType = kwargs.get("sceneType")
    wapUrl = kwargs.get("wapUrl")
    wapName = kwargs.get("wapName")
    # 场景信息
    sceneInfoDic = {
        "h5_info":{
            "type": sceneType,
            "wap_url": wapUrl,
            "wapName": wapName
        }
    }
    logger.debug(spbillCreateIp)
    logger.debug(sceneInfoDic)
    ret = {"status": "10000", "message": "Success"}
    wechatPay = WeChatPay(
        #  appid必须为最后拉起付款的应用appid；
        appid=appId,
        api_key=apiKey,
        # mch_id为和appid成对绑定的支付商户号，收款资金会进入该商户号；
        mch_id=mchId,
        # 沙箱模式，且在沙箱模式下订单金额固定为3.01
        sandbox=devConfig.WECHAT_SANDBOX
    )
    # 接收微信支付异步通知回调地址
    notifyUrl = devConfig.WECHAT_NOTIFY_URL
    # APP和网页支付提交用户端ip，Native、JSAPI支付填调用微信支付API的机器IP
    clientIp = "127.0.0.1"
    # 创建订单
    """ 
        openid为appid对应的用户标识，即使用wx.login接口获得的openid
        沙箱环境返回的支付二维码不可扫，仿真系统根据支付金额（total_fee字段）返回预期报文 给商户。同时，落地该笔请求数据。即不需要扫码即完成了模拟支付
        真实环境下该微信号已被封，无法完成测试
        OrderedDict([('return_code', 'SUCCESS'), ('return_msg', 'OK'), ('appid', 'wxbe1e428ef7c9d7e5'), 
        ('mch_id', '1573748631'), ('nonce_str', 'kaSQIz7UucIuD6AE'), ('sign', 'BAC6A9EF622906084C05B16D74AAE62B'), 

        ('result_code', 'SUCCESS'), ('prepay_id', 'wx14142249559581ce664c4ad91239221600'), ('trade_type', 'NATIVE'), 
        ('code_url', 'weixin://wxpay/bizpayurl?pr=XVYkWkV')])

        统一下单预创建，JSAPI支付需要上传openid
        openid是微信用户在公众号appid下的唯一用户标识（appid不同，则获取到的openid就不同），可用于永久标记一个用户，同时也是微信JSAPI支付的必传参数。
        https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/Wechat_webpage_authorization.html
    """
    try:
        """
            subject:商品描述，对应微信官方接口的body参数
            openid、spbill_create_ip、scene_info作为可选参数，根据不同的tradeType进行赋值
        """
        order = wechatPay.order.create(
            tradeType,
            subject,
            totalFee,
            notifyUrl,
            clientIp,
            out_trade_no=chnlSeqNo,
            openid=openId,
            spbill_create_ip=spbillCreateIp,
            scene_info=str(sceneInfoDic)
        )
        logger.info(order)
        returnCode = order.get("return_code")
        resultCode = order.get("result_code")
        resultMsg = "|".join([order.get("return_msg", ""), order.get("err_code_des", "")])
        # 当returnCode和resultCode都为SUCCESS时，才代表业务成功
        if returnCode == "SUCCESS" and resultCode == "SUCCESS":
            # 预支付交易会话标识
            prepayId = order.get("prepay_id")
            now = get_now("%Y%m%d %H%M%S")
            sDate, sTime = now.split(" ")
            with connection() as con:
                transInfo = [chnlSeqNo, sDate, sTime, token, abilityType, account, totalPay, subject, "00"]
                sql = "insert into uniplat_trans(chnl_seq_no,chnl_date,chnl_time,token,trans_type,account,total_pay,subject,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                logger.info("预登记微信支付交易流水")
                cnt = con.insertOne(sql, transInfo)
            # 微信扫码支付统一下单会返回支付二维码，JSAPI支付不会返回二维码
            if abilityType == "01":
                codeUrl = order.get("code_url")
                ret.update({"codeUrl": codeUrl})
            # mweb_url为拉起微信支付收银台的中间页面，可通过访问该url来拉起微信客户端，完成支付,mweb_url的有效期为5分钟。
            if abilityType == "05":
                mwebUrl = order.get("mweb_url")
                ret.update({"mwebUrl": mwebUrl})
            ret.update({"prepayId": prepayId})
        else:
            logger.info(f"微信统一下单交易预创建失败 {resultCode}:{resultMsg}")
            ret.update({"status": resultCode, "message": resultMsg})
    except WeChatPayException as e:
        logger.info("调用wechatpy接口异常：%s" % e)
        ret.update({"status": e.return_code, "message": e.return_msg})
    except Exception as e:
        logger.info("微信统一下单交易创建异常：%s" % e)
        ret.update({"status": "90009", "message": "微信统一下单交易预创建异常"})

    return ret


@uniplat.route('/uniplat/callBack/ali', methods=['post'])
def alipayCallback():
    logger.info("支付完成,支付宝支付结果通知回调")
    data = request.form.to_dict()
    # logger.info(data)
    # sign 不能参与签名验证
    signature = data.pop("sign")
    """
    data = {
            'app_id': '2016102000727260',
            'auth_app_id': '2016102000727260',
            'buyer_id': '2088102180270700',
            'buyer_logon_id': 'lny***@sandbox.com',
            'buyer_pay_amount': '1.00',
            'charset': 'utf-8',
            'fund_bill_list': '[{"amount":"1.00","fundChannel":"ALIPAYACCOUNT"}]',
            'gmt_create': '2020-08-27 15:06:22',
            'gmt_payment': '2020-08-27 15:06:57',
            'invoice_amount': '1.00',
            'notify_id': '2020082700222150657070700508567416',
            'notify_time': '2020-08-27 15:06:57',
            'notify_type': 'trade_status_sync',
            'out_trade_no': 'UNP20200827140258000007',
            'point_amount': '0.00',
            'receipt_amount': '1.00',
            'seller_email': 'ndancy6417@sandbox.com',
            'seller_id': '2088102180424770',
            'sign': 'lVLD+1fd6zbbWmhbWrYOJ5JuGd3b1frcECfRAheR1riXyacpQSUNFfo1LQwxZtP+1v8x4JfOjpw0uw1cVpe39vMHfH8rxlJxlg3H1gdz/fNh0NDBrJg93p34o3MmHk+2cCnSXRsPPGZNRzWebXYWmdN0MQx+F/xZsaWeDZj+T70vo/LDLNC0U4C7l+clh+JlEQKLiyHLO/bVL/qFItQgqpxl08nWJC/ZNgjNeXvJsQXql32CnLDIJFOLmM7607jId4eiaj/FVE+cmgKdJEFzWpTOALSZThrvYAn9w3mGSpy3/+TTErellx+NhynhvXFP7lvmfb3+BVhh70sVgufhTw==',
            'sign_type': 'RSA2',
            'subject': '毕业之家商家平台',
            'total_amount': '1.00',
            'trade_no': '2020082722001470700501535781',
            'trade_status': 'TRADE_SUCCESS',
            'version': '1.0'
        }
    """
    # 通过appid查询支付宝扫码付配置信息，主要是查询秘钥存储地址
    appId = data.get("app_id")
    try:
        with connection() as con:
            sql = f"select key_cert_path from uniplat_payconf where app_id = '{appId}'"
            keyCertPath = con.fetchone(sql)[0]
        # 读取应用私钥
        app_private_key_string = open(os.path.join(keyCertPath, 'app_private_key.pem')).read()
        # 读取支付宝公钥
        alipay_public_key_string = open(os.path.join(keyCertPath, 'ali_public_key.pem')).read()
        # 创建支付宝扫码支付对象
        alipay = AliPay(
            # 以下参数为沙箱测试的参数
            appid=appId,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True
        )
        """
            其验签步骤为： 
            第一步： 在通知返回参数列表中，除去sign、sign_type两个参数外，凡是通知返回回来的参数皆是待验签的参数。 
            第二步： 将剩下参数进行url_decode, 然后进行字典排序，组成字符串，得到待签名字符串： 
            第三步： 将签名参数（sign）使用base64解码为字节码串。 
            第四步： 使用RSA的验签方法，通过签名字符串、签名参数（经过base64解码）及支付宝公钥验证签名。 
            第五步：在步骤四验证签名正确后，必须再严格按照如下描述校验通知数据的正确性。 

            1、商户需要验证该通知数据中的out_trade_no是否为商户系统中创建的订单号； 
            2、判断total_amount是否确实为该订单的实际金额（即商户订单创建时的金额）； 
            3、校验通知中的seller_id（或者seller_email) 是否为out_trade_no这笔单据的对应的操作方（有的时候，一个商户可能有多个seller_id/seller_email）； 
            4、验证app_id是否为该商户本身。 

            上述1、2、3、4有任何一个验证不通过，则表明本次通知是异常通知，务必忽略。在上述验证通过后商户必须根据支付宝不同类型的业务通知，
            正确的进行不同的业务处理，并且过滤重复的通知结果数据。在支付宝的业务通知中，只有交易通知状态为TRADE_SUCCESS或TRADE_FINISHED时，支付宝才会认定为买家付款成功。 
            """
        success = alipay.verify(data, signature)
        if success and data["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            logger.info("支付宝通知回调，已完成付款")
            # 调用方流水号
            chnlSeqNo = data.get("out_trade_no")
            # 支付宝交易凭证号
            tradeNo = data.get("trade_no")
            # 买家ID
            buyerId = data.get("buyer_id")
            # 买家账号
            buyerLogonId = data.get("buyer_logon_id")
            # 支付时间，暂时用now来测试返回给支付宝的success是否成功
            # gmtPayment = data.get("gmt_payment")
            gmtPayment = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with connection() as con:
                sql = f"""update uniplat_trans set other_id = '{buyerId}',other_acct = '{buyerLogonId}',trade_no = '{tradeNo}',
                            status = '01',upd_time = '{gmtPayment}'
                                where chnl_seq_no = '{chnlSeqNo}'"""
                logger.info(f"更新交易流水表:{sql}")
                con.update(sql)
                # 预留通知买家的操作
                # 预留更新支付宝账户余额的操作
        else:
            # 可以打印出data内容，看看有没有什么返回信息可以输出的，这部分内容可以更新到表中，或者通知给付款方
            logger.info("支付宝支付通知回调，未完成付款")
    except Exception as e:
        logger.info(f"接收支付宝回调通知异常:{e}")
        # 向支付宝支付平台返回消息
    return Response('success')


@uniplat.route('/uniplat/callBack/wechat', methods=['post'])
def wechatpayCallback():
    logger.info("支付完成,微信支付结果通知回调")
    streamB = request.stream.read()
    # 解析微信支付平台回调时传的字节流
    root = xml(streamB)
    logger.info(streamB)
    returnCode = xmlread(root, "return_code")
    resultCode = xmlread(root, "result_code")
    resultMsg = "|".join([xmlread(root, "return_msg"), xmlread(root, "err_code_des")])
    try:
        # if returnCode == 'SUCCESS':
        if returnCode == "SUCCESS" and resultCode == "SUCCESS":
            # 微信支付单号
            transId = xmlread(root, "transaction_id")
            # 商户订单号，调用方流水号
            chnlSeqNo = xmlread(root, "out_trade_no")
            # 卖方用户标识,用户在商户appid下的唯一标识
            openid = xmlread(root, "openid")
            # 支付完成时间
            upd_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with connection() as con:
                sql = f"""update uniplat_trans set trade_no = '{transId}',status = '01',upd_time = '{upd_time}'
                            where chnl_seq_no = '{chnlSeqNo}'"""
                logger.info(f"更新交易流水表:{sql}")
                con.update(sql)
                # 预留通知买家的操作
                # 预留更新微信账户余额的操作
        else:
            logger.info(f"微信支付通知回调，未完成付款：{resultMsg}")
    except Exception as e:
        logger.info(f"接收支付宝回调通知异常：{e}")

    # 向微信支付平台返回消息
    res = "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"
    return res



@uniplat.route('/uniplat/trade/query', methods=['post'])
def queryOrder():
    """
    查询订单状态
    """
    logger.info("查询订单状态")
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
        "chnlTime": sTime
    })
    try:
        bizContent = data.get("bizContent")
        # 查询类别
        abilityType = head.get("abilityType")
        # 待查询的商户订单号
        orderSeqNo = bizContent.get("orderSeqNo")
        # 调用能力类型非空校验
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

        # 需要校验的报文体参数：
        if not orderSeqNo:
            returnMessage = "参数项[orderSeqNo]不能为空"
            logger.debug(returnMessage)
            head.update({
                "returnCode": "FAIL",
                "returnMessage": returnMessage
            })
            ret.update({
                "head": head
            })
            return jsonify(ret)
        # 查询本地数据库，获取交易结果
        with connection() as con:
            sql = f"""select trade_no,status from uniplat_trans
                        where chnl_seq_no = '{orderSeqNo}'"""
            logger.info(f"查询订单信息：{sql}")
            row = con.fetchone(sql)
            if not row:
                returnMessage = "未查询到相应订单，请确认订单流水号是否正确"
                logger.info(returnMessage)
                head.update({
                    "returnCode": "SUCCESS",
                    "returnMessage": "业务已受理"
                })
                ret = {
                    "head": head,
                    "bizContent": {
                        "status": "FAIL",
                        "message": returnMessage
                    }
                }
                return jsonify(ret)

            transId, status = row
            if status == "01":
                head.update({
                    "returnCode": "SUCCESS",
                    "returnMessage": "业务已受理"
                })
                bizContent.update({
                    "transId" : transId,
                    "status": "SUCCESS",
                    "message": "支付成功"
                    })
                ret.update({
                    "head": head,
                    "bizContent": bizContent
                })
                return jsonify(ret)
            else:
                logger.info("支付状态为00-预登记，可能未完成支付也可能未收到异步通知回调，准备查询服务方")
                sql = f"""select account,app_id,coalesce(mch_id,'') as mch_id,coalesce(api_key,'') as api_key,key_cert_path 
                        from uniplat_ability_conf
                            where ability_type = '{abilityType}'"""
                logger.info(f"查询收款信息，构建Pay对象：{sql}")
                row = con.fetchone(sql)
                if not row:
                    returnMessage = "未配置对应的收款信息"
                    logger.info(returnMessage)
                    head.update({
                        "returnCode": "FAIL",
                        "returnMessage": returnMessage
                    })
                    ret.update({
                        "head": head
                    })
                    return jsonify(ret)
                account, appId, mchId, apiKey, keyCertPath = row
                keyCertPath = os.path.join(devConfig.KEY_CERT_PRE_PATH,keyCertPath)
                if abilityType == "00":
                    logger.info("通过支付宝开放平台查询订单状态，未开通")
                    pass
                elif abilityType == "03":
                    logger.info("通过微信开放平台查询订单状态")
                    wechatPay = WeChatPay(
                        #  appid必须为最后拉起付款的应用appid；
                        appid=appId,
                        api_key=apiKey,
                        # mch_id为和appid成对绑定的支付商户号，收款资金会进入该商户号；
                        mch_id=mchId,
                        # 沙箱模式，且在沙箱模式下订单金额固定为3.01
                        sandbox=devConfig.WECHAT_SANDBOX
                    )
                    """
                        OrderedDict([('return_code', 'SUCCESS'), ('return_msg', 'OK'), ('appid', 'wx160ceb97b57aaf94'), 
                        ('mch_id', '1605655760'), ('device_info', None), ('nonce_str', 'F4Rf0glRi6p8fjUo'), 
                        ('sign', '1E522268CB750E0AB590A1E9EF6D56D6'), ('result_code', 'SUCCESS'), ('total_fee', '10'), 
                        ('out_trade_no', 'UNP2021011219000000009'), ('trade_state', 'NOTPAY'), ('trade_state_desc', '订单未支付')])
                    """
                    queryObj = wechatPay.order.query(
                        transaction_id = transId,
                        out_trade_no = orderSeqNo
                        )
                    return_code = queryObj.get("return_code")
                    return_msg = queryObj.get("return_msg")
                    if return_code == "SUCCESS":
                        trade_state = queryObj.get("trade_state")
                        trade_state_desc = queryObj.get("trade_state_desc")
                        if trade_state == "SUCCESS":
                            transaction_id = queryObj.get("transaction_id")
                            # 支付完成时间
                            upd_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            sql = f"""update uniplat_trans set status = '01',trade_no = '{transaction_id}',upd_time = '{upd_time}'
                                        where chnl_seq_no = '{orderSeqNo}'"""
                            logger.info(f"支付成功，更新订单表状态:{sql}")
                            con.update(sql)
                        else:
                            transaction_id = ""
                            logger.info(trade_state_desc)
                    else:
                        transaction_id = ""
                        logger.info(return_msg)
                    head.update({
                        "returnCode": return_code,
                        "returnMessage": return_msg
                    })
                    bizContent.update({
                        "transId": transaction_id,
                        "status": trade_state,
                        "message": trade_state_desc
                        })
                    ret.update({
                        "head": head,
                        "bizContent": bizContent
                    })
                    return jsonify(ret)
    except WeChatPayException as e:
        logger.info("调用wechatpy接口异常：%s" % e)
        head.update({
            "returnCode": e.return_code,
            "returnMessage": e.return_msg
        })
        ret.update({
            "head": head
        })
    except Exception as e:
        logger.info("查询订单状态异常：%s" % e)
        head.update({
            "returnCode": "FAIL",
            "returnMessage": "查询订单状态异常"
        })
        ret.update({
            "head": head
        })
    return jsonify(ret)

def notice_by_rmq(exchange, routing_key, body):
    """
        通过RMQ异步通知消息
    """
    # 使用消息队列通知前端 RMQ连接参数
    CONN_PARAM = devConfig.MQS_CONNECTION_PARAMETER
    user, pwd = CONN_PARAM.get('user_name'), CONN_PARAM.get('pass_word')
    # 创建证书
    credentials = pika.PlainCredentials(user, pwd)
    # 创建连接
    conn = pika.BlockingConnection(pika.ConnectionParameters(CONN_PARAM.get('host'), credentials=credentials))
    # 在连接上创建一个频道
    channel = conn.channel()
    # 向指定的exchange发布消息，并指定路由规则
    channel.basic_publish(exchange=exchange,
                          routing_key=routing_key,
                          body=body)
    # 关闭链接
    conn.close()







