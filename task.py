import base64
import hashlib
import os
import re
import threading
import time
from _md5 import md5
from concurrent.futures import ThreadPoolExecutor, Future

from lxml import etree
from flask import current_app

import github
from handler import telegram_api

import logging

logging = logging.getLogger(__name__)


def payloadPatterns(patterns, content, url):
    result = {'url': url}
    hit = []
    # 判断是否存在Payload
    if len(patterns) > 0:

        for p in patterns:
            data = p['pattern'].findall(content)
            if len(data) > 0:
                payloadResult = []
                for pData in data:
                    payloadResult.append(pData)
                hit.append({p['id']: payloadResult})
    result['data'] = hit
    return result


def run(self):
    self._running = True
    self.func()
    while self._running:
        if self.taskData.pollingPage > 0 and self._running:
            time.sleep(self.taskData.cycle)
            self.func(False)


class Task(object):

    def __init__(self, taskData, payloads, exchange, thread_pool: ThreadPoolExecutor):
        self.taskData = taskData
        self.payloads = payloads
        self._running = False
        self.exchange = exchange
        self.thread_pool = thread_pool
        self.future: Future = None

    def func(self, first=True):
        global page
        g = github.Github()
        patterns = []
        for payload in self.payloads:
            patterns.append({'pattern': re.compile(payload.payload, re.S), 'id': payload.id})
            page = 10
            if first:
                page = self.taskData.endPage
            else:
                page = self.taskData.pollingPage

        for i in range(1, page):
            if not self._running:
                logging.debug('任务结束')
                break

            taskUrl = 'https://github.com/search?q=%s&type=Code&p=%s' % (self.taskData.query.replace(' ', '+'), i)
            resultList = None
            try:
                resultList = g.get(taskUrl, r=True)
                if resultList[0] is None:
                    telegram_api.sendMessage('❌ 分页数据获取异常，已停止任务\n<code>%s</code>' % resultList[1])
            except Exception as e:
                telegram_api.sendMessage('❌ 分页数据获取异常，已停止任务\n<code>%s</code>' % e.__str__())
                self._running = False
                return

            dom_tree_code = etree.HTML(resultList[0].text)
            # 获取存在信息泄露的链接地址
            urls = dom_tree_code.xpath('//div[@class="f4 text-normal"]/a/@href')
            if len(urls) == 0:
                # 未找到数据
                logging.debug('数据循环结束，进行下一轮')
                break
            contents = dom_tree_code.xpath(
                '//div[@class="hx_hit-code code-list-item d-flex py-4 code-list-item-public "]')
            for i in range(0, len(urls)):
                url = urls[i]
                if self.taskData.openUrl == 1:
                    # 打开内页探索模式
                    url = 'http://hub.object.cool' + url.replace('/blob', '')
                    insideResult = None
                    try:
                        insideResult = g.get(url, r=True)
                    except Exception as e:
                        telegram_api.sendMessage('❌ 内页数据获取异常，已停止任务\n<code>%s</code>' % e.__str__())
                        self._running = False
                        return

                    hl = hashlib.md5()
                    hl.update(url.encode('utf-8'))
                    fileName = 'cache/' + hl.hexdigest()
                    if not os.path.exists(fileName):
                        f = open(fileName, 'w')
                        f.write(insideResult[0].text)
                        f.close()
                    result = payloadPatterns(patterns, insideResult[0].text, url)
                    result['type'] = 'inside'
                    result['taskId'] = self.taskData.id
                    self.exchange.send(result)
                    # 内页数据延迟半秒获取
                    time.sleep(0.5)
                else:

                    hl = hashlib.md5()
                    hl.update(url.encode('utf-8'))
                    fileName = 'cache/' + hl.hexdigest()
                    if not os.path.exists(fileName):
                        f = open(fileName, 'w')
                        f.write(contents[i])
                        f.close()
                    # 外页探索模式
                    self.exchange.send({'type': 'outside', 'url': url, 'taskId': self.taskData.id})

    # 停止任务
    def stop(self):
        self._running = False
        try:
            if self.future is not None:
                self.future.result(10)
                self.future = None
            return True
        except:
            return False

    # 重启任务
    def restart(self):
        if self.stop():
            self.start()
            return True
        else:
            return False

    def start(self):
        if self.future is None:
            self.future = self.thread_pool.submit(run, self)

    # 任务当前信息
    def info(self):
        return {'taskId': self.taskData.id, 'isRuning': self._running}

    def send(self, msg):
        func = msg['func']
        if func == 'changeData' and msg['taskId'] == self.taskData.id:
            if self.stop():
                self.taskData = msg['taskData']
                self.payloads = msg['payloads']
                self.start()
                return True
            else:
                return False
        elif func == 'start' and msg['taskId'] == self.taskData.id:
            self.start()
            return True
        elif func == 'stop' and msg['taskId'] == self.taskData.id:
            return self.stop()

        return None
