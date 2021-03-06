import configparser
import threading
import time
from queue import Queue
from time import sleep
from lxml import etree

import requests

from handler import telegram_api

import logging

logging = logging.getLogger(__name__)

request_lock = threading.Event()


class Github(object):
    _instance = None
    queue = Queue(3)

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.session = self.login()

    def post(self, url, data=None, json=None, **kwargs):
        if request_lock.is_set():
            request_lock.wait()
        result = self.session.post(url, data, json, **kwargs)
        if result.text.find('Sign in to GitHub · GitHub') > 0:
            self.session = self.login()
            return self.post(url, data, json, **kwargs)
        else:
            return result

    def get(self, url, **kwargs):
        if request_lock.is_set():
            request_lock.wait()
        try:
            result = self.session.get(url)
            if result.text.find('Sign in to GitHub · GitHub') > 0:
                self.session = self.login()
                return self.get(url, **kwargs)
            else:
                return result, ''
        except Exception as e:
            logging.error('请求失败,URL:%s 错误信息:%s' % (url, e.__str__()))
            if not kwargs.get('r', False):
                return None, '请求失败,URL:%s 错误信息:%s' % (url, e.__str__())
            else:
                error = kwargs.get('error')
                if error is None:
                    error = 0
                if error > 5:
                    raise Exception(e.__str__())
                return self.get(url=url, error=error + 1, **kwargs)

    def reLogin(self):
        self._instance = None
        logging.debug('登录失效，重新登录')

    # 登陆Github
    def login(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        # 初始化参数
        login_url = 'https://github.com/login'
        session_url = 'https://github.com/session'
        verified_device = 'https://github.com/sessions/verified-device'
        try:
            # 获取session
            s = requests.session()
            resp = s.get(login_url).text
            dom_tree = etree.HTML(resp)
            key = dom_tree.xpath('//input[@name="authenticity_token"]/@value')
            user_data = {
                'commit': 'Sign in',
                'utf8': '✓',
                'authenticity_token': key,
                'login': config['GITHUB']['username'],
                'password': config['GITHUB']['password']
            }
            sleep(0.5)
            # 发送数据并登陆
            loginResult = s.post(session_url, data=user_data)
            if loginResult.headers.get('Location') == 'https://github.com/sessions/verified-device':
                request_lock.set()
                telegram_api.sendMessage('Github 登录异常，您已收到一封登录邮件。验证码输入格式:code-123456 / 重新获取格式:code-new')
                tokenGet = s.get(verified_device)
                tokenGetDom = etree.HTML(resp)
                key = tokenGetDom.xpath('//input[@name="authenticity_token"]/@value')
                codeFunc = Github.queue.get()
                codeFuncs = codeFunc.split("-")
                if 'new' != codeFuncs[1]:
                    res = s.post({'authenticity_token': key, 'otp': codeFuncs[1]})
                    if res.status_code == 200 or res.text.find('Incorrect verification code provided.') > -1:
                        telegram_api.sendMessage('验证码错误，尝试重新登录')
                request_lock.clear()

            sleep(0.5)
            r = s.get('https://github.com/settings/profile')
            rs = r.text.find('Sign in to GitHub · GitHub')
            if rs > -1:
                logging.debug('登录失败，正在重试')
                return self.login()
            return s
        except Exception as e:
            logging.debug('登录失败，正在重试:', e.__str__())
            return self.login()
