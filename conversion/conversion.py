import os
import threading


class Conversion:
    con = threading.Condition()

    def __init__(self):
        self.plugins = {}
        self.loadPlugins()

    def loadPlugins(self):
        Conversion.con.acquire()
        for filename in os.listdir("conversion/plugins"):
            if not filename.endswith(".py") or filename.startswith("_") or not filename.startswith(
                    'plugin') or filename.find('_') == -1:
                continue
            self.runPlugin(filename)
        Conversion.con.release()

    def runPlugin(self, filename):
        pluginName = os.path.splitext(filename)[0]
        plugin = __import__("conversion.plugins." + pluginName, fromlist=[pluginName])
        clazz = plugin.getPluginClass()
        o = clazz
        plugin_name = pluginName.split("_")[1]
        self.plugins[plugin_name] = {'plugin': o, 'desc': o.desc()}

    def hit(self, data, plugin_name, url):
        Conversion.con.acquire()
        # 等待插件加载
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]['plugin'].run(data, url)
        Conversion.con.release()


conversion = Conversion()
