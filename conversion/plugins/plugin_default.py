class DefaultPlugin:
    def run(self, data, url):
        return data

    def desc(self):
        return "EOS 默认插件"

    def version(self):
        return '<v>1.0.0</v>'


def getPluginClass():
    return DefaultPlugin()
