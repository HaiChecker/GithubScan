import re
import threading
import time

from lxml import etree
from flask import current_app

import github


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


class Task(threading.Thread):

    def __init__(self, taskData, payloads, exchange):
        threading.Thread.__init__(self, name='Task:%d' % taskData.id)
        self.taskData = taskData
        self.payloads = payloads
        self._running = False
        self.exchange = exchange

    def run(self):
        self._running = True
        print('开始执行任务:', self.taskData.id)
        self.func()
        while self._running:
            if self.taskData.pollingPage > 0 and self._running:
                time.sleep(self.taskData.cycle)
                self.func(False)

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
                print('任务结束')
                break

            taskUrl = 'https://github.com/search?q=%s&type=Code&p=%s' % (self.taskData.query.replace(' ', '+'), i)
            resultList = g.get(taskUrl)

            dom_tree_code = etree.HTML(resultList.text)
            # 获取存在信息泄露的链接地址
            urls = dom_tree_code.xpath('//div[@class="f4 text-normal"]/a/@href')
            contents = dom_tree_code.xpath(
                '//div[@class="hx_hit-code code-list-item d-flex py-4 code-list-item-public "]')
            for i in range(0, len(urls)):
                url = urls[i]
                if self.taskData.openUrl == 1:
                    # 打开内页探索模式
                    url = 'https://raw.githubusercontent.com' + url.replace('/blob', '')
                    insideResult = g.get(url)
                    result = payloadPatterns(patterns, insideResult.text, url)
                    result['type'] = 'inside'
                    result['taskId'] = self.taskData.id
                    self.exchange.send(result)
                else:
                    # 外页探索模式
                    self.exchange.send({'type': 'outside', 'url': url, 'taskId': self.taskData.id})

    # 停止任务
    def stop(self):
        self._running = False
        self.join()

    # 重启任务
    def restart(self):
        self.stop()
        self.start()

    # 任务当前信息
    def info(self):
        pass

    def send(self, msg):
        func = msg['func']
        if func == 'changeData' and msg['taskId'] == self.taskData.id:
            self.stop()
            self.taskData = msg['taskData']
            self.payloads = msg['payloads']
            self.start()
        elif func == 'start' and msg['taskId'] == self.taskData.id:
            self.start()
        elif func == 'stop' and msg['taskId'] == self.taskData.id:
            self.stop()
