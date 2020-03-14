import threading

from hashlib import md5

from queue import Queue

from sqlalchemy.orm import sessionmaker

from conversion import conversion
from db import models
from db.models import HHit, HConfig, HPayload
from handler import telegram_api

q = Queue(1024)


class Handler(object):
    plugins = {}

    def getPluginName(self, payloadId):
        if payloadId in Handler.plugins:
            return Handler.plugins[payloadId]
        else:
            try:
                payload = self.getDbSession().query(HPayload).filter(HPayload.id).one()
                return payload.plugin
            except:
                return None

    def getDbSession(self):
        if self._session is None:
            engine = models.getDb()
            Session = sessionmaker(bind=engine)
            self._session = Session()
        return self._session

    def __init__(self):
        self._session = None

    def run(self):
        while True:
            msg = q.get()
            taskId = msg['taskId']
            msgType = msg['type']
            url = msg['url']
            notify = self.getDbSession().query(HConfig).filter(HConfig.k == 'notify').one()
            if msgType == 'inside':
                # 内页数据
                data = msg['data']
                if len(data) > 0:
                    for payloadDatas in data:
                        for payloadData in payloadDatas:
                            payloadId = payloadData

                            for hit in payloadDatas[payloadId]:
                                md5Hash = md5()
                                md5Hash.update(str(taskId).encode('utf-8'))
                                md5Hash.update(hit.encode('utf-8'))
                                hashStr = md5Hash.hexdigest()

                                result = conversion.conversion.hit(hashStr, payloadId, url)
                                if result is not None:
                                    hitCount = self.getDbSession().query(HHit) \
                                        .filter(HHit.hitHash == hashStr) \
                                        .count()
                                    if hitCount <= 0:

                                        hit = HHit(tid=taskId, pid=payloadId, url=url, hit=hit, hitHash=hashStr)
                                        self.getDbSession().add(hit)
                                        self.getDbSession().commit()
                                        if notify.v == 'Y':
                                            telegram_api.sendNotify(hit)




            else:
                # 外页数据

                md5Hash = md5()
                md5Hash.update(url.encode('utf-8'))
                md5Hash.update(str(taskId).encode('utf-8'))
                hashStr = md5Hash.hexdigest()
                hitCount = self.getDbSession().query(HHit) \
                    .filter(HHit.hitHash == hashStr) \
                    .count()
                if hitCount <= 0:
                    self.getDbSession().add(HHit(tid=taskId, pid=-1, url=url, hit=url, hitHash=hashStr))
                    self.getDbSession().commit()

    def send(self, msg):
        q.put(msg)
