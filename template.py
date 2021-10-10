# -*- coding:utf8 -*-
#from wechatpy.client.api import WeChatTemplate
import requests,json
access_token = '19_utqi5hWrq_-nAJJAwx6jJZfswbrr2wA4WRK_gF452sfQbN5oIqIA2tm5_NBhbPEC1Xes_AEQHp8MNwiR6mpLWXKOFf2yXJCzqkGomnf8q5lFE3j5bjvd5E0bT7PMWKe_R0UgqLvO2ag8zUSsOLNdACAFCE'
url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}'.format(ACCESS_TOKEN = access_token)
print(url)
data = {
           "touser":"oZMcI592WXfjDChKEnvjuvTkg-VY",
           "template_id":"MMkej4RBxn_vD8bsF7eT1QlT8vWEB-2BTxDUGGu5y_U",         
           "data":{
                   "title": {
                       "value":"测试会议主题！",
                   },
                   "time":{
                       "value":"测试会议时间",
                   },
                   "person": {
                       "value":"测试参与人员",
                   },
                   "content": {
                       "value":"测试会议内容",
                   },
                   "context":{
                       "value":"测试联系人！",
                   }
           }
       }
r = requests.post(url, data=json.dumps(data))
print(r.json())