class DefaultPlugin:
    def run(self, data):
        return data


def getPluginClass():
    return DefaultPlugin


def desc():
    return "EOS 默认插件"
