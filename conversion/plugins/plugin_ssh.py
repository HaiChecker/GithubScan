import hashlib


class EosPlugin:
    """
    ((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}
    """

    def run(self, data, url):
        hl = hashlib.md5()
        hl.update(url.encode('utf-8'))

        fileName = 'cache/' + hl.hexdigest()
        line = ''
        with open(fileName, 'r') as f:
            line = line + f.readline()
        if line.find('password') > -1 or line.find('port') > -1 or line.find('host') > -1:
            return data
        else:
            return None

    def desc(self):
        return "服务器泄漏查询"

    def version(self):
        return '<v>1.0.0</v>'


def getPluginClass():
    return EosPlugin()
