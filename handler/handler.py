import threading

from hashlib import md5

from queue import Queue

from sqlalchemy.orm import sessionmaker

from conversion import conversion
from db import models
from db.models import HHit, HConfig, HPayload
from handler import telegram_api
import logging

logging = logging.getLogger(__name__)

q = Queue(1024)


def run(self):
    while True:
        try:
            logging.debug('准备获取数据')
            msg = q.get()
            logging.debug('获取到数据:%s' % msg)
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
                                if type(hit) is not str:
                                    continue
                                md5Hash = md5()
                                md5Hash.update(str(taskId).encode('utf-8'))
                                md5Hash.update(hit.encode('utf-8'))
                                hashStr = md5Hash.hexdigest()

                                result = conversion.conversion.hit(hashStr, self.getPluginName(payloadId), url)
                                if result is not None:
                                    hitCount = self.getDbSession().query(HHit) \
                                        .filter(HHit.hitHash == hashStr) \
                                        .count()
                                    if hitCount <= 0:

                                        hitDb = HHit(tid=taskId, pid=payloadId, url=url, hit=hit, hitHash=hashStr)
                                        self.getDbSession().add(hitDb)
                                        self.getDbSession().commit()
                                        logging.debug('写入数据库成功')
                                        if notify.v == 'Y':
                                            telegram_api.sendNotify(hit)
                                else:
                                    logging.debug('脚本验证失败')
                else:
                    logging.debug('没有数据')



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
        except Exception as e:
            logging.error('数据处理异常:%s' % e.__str__())


class Handler(object):
    plugins = {}

    def getPluginName(self, payloadId):
        if payloadId in Handler.plugins:
            return Handler.plugins[payloadId]
        else:
            try:
                payload = self.getDbSession().query(HPayload).filter(HPayload.id == payloadId).one()
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

    def send(self, msg):
        q.put(msg)
