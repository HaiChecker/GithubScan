import base64
import hashlib


class MysqlPlugin:
    """
    ((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}
    """

    def run(self, data, url):
        if type(data) is not str:
            print(data + '  --  ' + type)
            return None
        hl = base64.b32encode(url.encode('utf-8')).decode('utf-8')

        if data.find('localhost') > -1 or data.find('127.0.0.1'):
            return None

        fileName = 'cache/' + hl
        f = open(fileName, 'r')
        line = "\n".join(f.readlines())
        if line.find('password') > -1 or line.find('port') > -1 or line.find('host') > -1:
            return data
        else:
            print('未找到')
            return None

    def desc(self):
        return "服务器泄漏查询"

    def version(self):
        return '<v>1.0.1</v>'


def getPluginClass():
    return MysqlPlugin()
