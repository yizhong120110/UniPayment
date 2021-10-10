# -*- coding:utf8 -*-
from fdfs_client.client import Fdfs_client, get_tracker_conf
from utils.log.logger import log as app_log
from settings import DevelopmentConfig as DEVConfig

logger = app_log.log
devConfig = DEVConfig()

class FastDFSStorage():
    def __init__(self,client_conf = None):
        if client_conf == None:
            client_conf = devConfig.FDFS_CLIENT_CONF
        self.client_conf = client_conf
    
    def uploadByName(self,fullFileName):
        trackers = get_tracker_conf(self.client_conf)
        client = Fdfs_client(trackers)
        result = client.upload_by_filename(fullFileName)
        return result