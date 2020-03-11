from db import models
from db.db import IScanDB


class MySqlDb(IScanDB):
    def init(self, data):
        self.engine = models.createMysql(data['dbUser'], data['dbUserPwd'], data['dbHost'], data['dbPort'], data['dbName'])

    def addTask(self, task):
        pass

    def removeTask(self, taskId):
        pass

    def getAllTask(self):
        pass

    def getTaskByWhere(self, where):
        pass
