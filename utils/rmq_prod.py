# coding:utf8
import pika,json
import sys

username = 'zsdev'
pwd = 'zsdev'
credentials  = pika.PlainCredentials(username, pwd)
#创建连接
conn = pika.BlockingConnection(pika.ConnectionParameters( '47.104.231.221', credentials = credentials) )
#在连接上创建一个频道
channel = conn.channel()  

channel.exchange_declare(exchange='wechatpay',exchange_type='topic')  # 创建模糊匹配类型的exchange。。

routing_key = 'wechatpay.*'##这里关键字必须为点号隔开的单词，以便于消费者进行匹配。引申：这里可以做一个判断，判断产生的日志是什么级别，然后产生对应的routing_key，使程序可以发送多种级别的日志
#message =  'Hello World!'
message = json.dumps( {"code" : 200 , "msg" : "支付成功" , "vip" : "true" } )
#message = {"code" : 200 , "msg" : "支付成功" , "vip" : "true" }
channel.basic_publish(exchange='wechatpay',#将交换机、关键字、消息进行绑定
                      routing_key=routing_key,  # 绑定关键字，将队列变成[warn]日志的专属队列
                      body=message)
print(" [x] Sent %r:%r" % (routing_key, message))
conn.close()