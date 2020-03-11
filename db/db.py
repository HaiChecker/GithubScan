import configparser
from abc import ABCMeta, abstractmethod

from db.mysql_db import MySqlDb


class IScanDB(metaclass=ABCMeta):

    def __init__(self):
        self.engine = None

    # 初始化数据库
    @abstractmethod
    def init(self, data):
        pass

    @abstractmethod
    def addTask(self, task):
        pass

    @abstractmethod
    def removeTask(self, taskId):
        pass

    @abstractmethod
    def getAllTask(self):
        pass

    @abstractmethod
    def getTaskByWhere(self, where):
        pass




