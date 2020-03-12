import configparser
from time import sleep
from lxml import etree

import requests


class Github(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.session = self.login()

    def post(self, url, data=None, json=None, **kwargs):
        result = self.session.post(url, data, json, **kwargs)
        if result.text.find('Sign in to GitHub · GitHub') > 0:
            self.session = self.login()
            return self.post(url, data, json, **kwargs)
        else:
            return result

    def get(self, url, **kwargs):
        try:
            result = self.session.get(url, **kwargs)
            if result.text.find('Sign in to GitHub · GitHub') > 0:
                self.session = self.login()
                return self.get(url, **kwargs)
            else:
                return result, ''
        except Exception as e:
            print('请求失败,URL:%s 错误信息:%s' % (url, e.__str__()))
            if not kwargs.get('r', False):
                return None, '请求失败,URL:%s 错误信息:%s' % (url, e.__str__())
            else:
                error = kwargs.get('error', 0)
                if error > 5:
                    raise Exception(e.__str__())
                return self.get(url=url, error=error + 1, **kwargs)

    def reLogin(self):
        self._instance = None
        print('登录失效，重新登录')

    # 登陆Github
    def login(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        # 初始化参数
        login_url = 'https://github.com/login'
        session_url = 'https://github.com/session'

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
            s.post(session_url, data=user_data)
            sleep(0.5)
            r = s.get('https://github.com/settings/profile')
            rs = r.text.find('Sign in to GitHub · GitHub')
            if rs > -1:
                print('登录失败，正在重试')
                return self.login()
            return s
        except Exception as e:
            print('登录失败，正在重试:', e.__str__())
            return self.login()
