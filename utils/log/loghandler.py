# -*- coding: utf-8 -*-
import logging,time

class DateFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a"):
        self.bf = filename
        self.curDate = time.strftime('%Y%m%d', time.localtime())
        self.mode = mode
        t = time.time()
        filename = filename + '_' + self.curDate + '.log'
        logging.FileHandler.__init__(self, filename, mode)

    def emit(self, record):
        cd = time.strftime('%Y%m%d', time.localtime())
        if cd != self.curDate:
            self.stream.close()
            self.curDate = cd
            self.stream = open(self.bf + '.' + cd, self.mode)
        logging.FileHandler.emit(self, record)
