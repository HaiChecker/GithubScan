# interfaces.py
class Plugin:
    def run(self, hit):
        pass

    def desc(self):
        return "插件说明"

    def version(self):
        return "<v>版本号</v>"


def getPluginClass():
    pass
