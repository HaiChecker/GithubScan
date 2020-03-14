import base64
import configparser
import json
import logging
import os
import re
import threading

import requests
from sqlalchemy.orm import sessionmaker
from telebot import apihelper
from telebot import types

import telebot

import github
from conversion import conversion
from db import models
from db.models import HConfig

config = configparser.ConfigParser()
config.read('config.ini')

if config['WEB']['proxy']:
    apihelper.proxy = {'https': config['WEB']['proxy']}

apihelper.API_URL = config['TELEGRAM']['apiUrl']
apihelper.FILE_URL = config['TELEGRAM']['fileUrl']

bot = telebot.TeleBot(config['TELEGRAM']['token'])

addTaskJson = json.loads(
    '{"func":"addTask","data":{"query":"eos wallet","startPage":1,"endPage":100,"type":"polling","cycle":3600,'
    '"pollingPage":6,"run":true, '
    '"openUrl":1,"payloads":[1,2,3]}}')

addPayloadJson = json.loads('{"func":"addPayload","data":[{"title": "EOS私钥匹配","payload": "正则1","plugin":"插件名称"}]}')

bashUrl = 'http://' + config['WEB']['host'] + ':' + config['WEB']['port']


def payloadList():
    result = requests.get(bashUrl + '/payloadList')
    payloadsJson = json.loads(result.text)
    if payloadsJson['code'] == 200:
        payloads = payloadsJson['data']
        resultStr = []
        for payload in payloads:
            em = '🎯'
            pStr = 'ID:%s 说明:%s 命中:%s个' % (payload['id'], payload['title'], payload['hit'])
            if payload['hit'] > 0:
                pair = json.dumps({'id': payload['id'], 'func': 'hit'})
                pairStr = base64.b64encode(pair.encode('utf-8')).decode("utf-8")
                pStr += ' [命中列表](http://t.me/GitHubScanBot?start=%s)' % pairStr
            else:
                pStr += ' 没有命中'
                em = '⚠️'
            resultStr.append(em + ' ' + pStr)
        return "\n".join(resultStr) if len(resultStr) > 0 else '❌ 您没有Payload哦'
    else:
        return payloadsJson['msg']


def addTask(data):
    result = requests.post(bashUrl + '/addTask', json=data)
    return json.loads(result.text)['msg']


def delete_task(data):
    result = requests.post(bashUrl + '/delTask', json=[data])
    return json.loads(result.text)['msg']


def addPayload(data):
    result = requests.post(bashUrl + '/addPayload', json=data)
    return json.loads(result.text)['msg']


def notify(chatId):
    result = requests.get(bashUrl + '/notify?chatId=%s' % chatId)
    return json.loads(result.text)['msg']


def hitList(id):
    result = requests.post(bashUrl + '/hit', json={'id': id})
    hitJson = json.loads(result.text)
    if hitJson['code'] == 200:
        hits = hitJson['data']
        resultStr = []
        for hit in hits:
            url = 'URL:[跳转到Github](%s) \n命中:%s' % (hit['url'], hit['hit'])
            resultStr.append(url)
        return "\n\n".join(resultStr) if len(resultStr) > 0 else '❌ 您没有命中哦'

    else:
        return hitJson['msg']


def startTask(id):
    result = requests.post(bashUrl + '/start', json=[id])
    return json.loads(result.text)['msg']


def stopTask(id):
    result = requests.post(bashUrl + '/stop', json=[id])
    return json.loads(result.text)['msg']


def taskList():
    result = requests.get(bashUrl + '/taskList')
    tasksJson = json.loads(result.text)
    resultStr = []
    if tasksJson['code'] == 200:
        tasks = tasksJson['data']
        for t in tasks:
            pair = json.dumps({'taskId': t['id'], 'func': 'stop' if t['isRun'] else 'start'})
            pairStr = base64.b64encode(pair.encode('utf-8')).decode("utf-8")

            hitPair = json.dumps({'id': t['id'], 'func': 'hit'})
            hitPairStr = base64.b64encode(hitPair.encode('utf-8')).decode("utf-8")

            deletePair = json.dumps({'id': t['id'], 'func': 'delete'})
            deletePairStr = base64.b64encode(deletePair.encode('utf-8')).decode("utf-8")

            hitStr = '[没有命中]' if t['hit'] == 0 else '[命中列表](http://t.me/GitHubScanBot?start=%s)' % hitPairStr

            resultStr.append('%s %s %s 命中:%s个 %s %s' % ('🟢' if t['isRun'] else '🔴', t['query'],

                                                        hitStr, t['hit'], ('[停止]' if t[
                'isRun'] else '[开始]') + '(http://t.me/GitHubScanBot?start=%s)' % pairStr,
                                                        '[删除](http://t.me/GitHubScanBot?start=%s)' % deletePairStr))
        return "\n".join(resultStr) if len(resultStr) > 0 else '❌ 您没有任务哦'
    else:
        return tasksJson['msg']


def sendNotify(hit):
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()

    chat = session.query(HConfig).filter(HConfig.k == 'chat_id').one()

    if chat.v != 0:
        bot.send_message(chat.v, hit)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "plugin-load":
        conversion.conversion.loadPlugins()
        bot.answer_callback_query(call.id, "刷新插件成功")
    elif call.data == "plugin-list":
        plugins = os.listdir("conversion/plugins")
        resultText = []
        for plugin in plugins:
            if not plugin.endswith(".py") or plugin.startswith("_") or not plugin.startswith(
                    'plugin') or plugin.find('_') == -1:
                continue
            try:
                plugin_name = os.path.splitext(plugin)[0].split("_")[1]
                fileVersion = '未导入'
                if plugin_name in conversion.conversion.plugins:

                    my_open = open('conversion/plugins/' + plugin, 'r')
                    # 若文件不存在,报错，若存在，读取
                    for eachline in my_open:
                        str = eachline.strip()
                        result = re.findall('<v>(.*)</v>', str)
                        if len(result) > 0:
                            fileVersion = result[0]
                            break
                    my_open.close()

                    if fileVersion == '未导入':
                        fileVersion = '版本异常'

                runVersion = '未导入'
                if plugin_name in conversion.conversion.plugins:
                    str = conversion.conversion.plugins[plugin_name][
                        'plugin'].version()
                    result = re.findall('<v>(.*)</v>', str)
                    if len(result) > 0:
                        runVersion = result[0]

                resultText.append('<code>%s 插件名:%s\t\t文件版本:%s\t\t运行版本:%s</code>' % (
                    plugin_name, fileVersion, runVersion, '✅ ' if fileVersion == runVersion else '❌ '))

            except Exception as e:
                logging.error('异常:%s' % e.__str__())
                continue

        if len(resultText) == 0:
            bot.answer_callback_query(call.id, "❌ 您没有插件哦")
            return
        engine = models.getDb()
        Session = sessionmaker(bind=engine)
        session = Session()

        chat = session.query(HConfig).filter(HConfig.k == 'chat_id').one()

        if int(chat.v) != 0:
            bot.answer_callback_query(call.id)
            bot.send_message(chat.v, "\n\n".join(resultText), parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ 请打开通知")


def sendMessage(msg):
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()

    chat = session.query(HConfig).filter(HConfig.k == 'chat_id').one()

    if int(chat.v) != 0:
        bot.send_message(chat.v, msg, parse_mode='HTML')


@bot.message_handler(commands=['plugin'])
def pluginMessage(msg):
    if msg.from_user.username == config['TELEGRAM']['receive']:
        text = msg.text
        entities = msg.entities
        texts = text.split(" ")
        if text == '/plugin' and len(entities) == 1 and entities[0].type == 'bot_command':
            markup = types.InlineKeyboardMarkup()
            refButton = types.InlineKeyboardButton('加载插件', callback_data='plugin-load')
            listButton = types.InlineKeyboardButton('插件列表', callback_data='plugin-list')
            markup.add(refButton, listButton)
            bot.send_message(msg.chat.id, '🛠插件管理', reply_markup=markup)

    else:
        bot.send_message(msg.chat.id, '⚠️您没有权限使用此服务哦')


def test_message(msg):
    return msg.document.mime_type == 'text/x-python'


def testPlugin(pluginStr):
    pluginStr = pluginStr.decode(
        'utf-8') + '\n\n\n\n\n' + "import json\nprint(json.dumps({'desc': desc(), 'result': getPluginClass().run(" \
                                  "'test')})) "
    try:
        eval(pluginStr)
        return True
    except:
        return False


@bot.message_handler(content_types=['document'])
def plugin(msg):
    if not test_message(msg):
        return
    try:
        bot.reply_to(msg, '❇️ 正在接收中')
        file_info = bot.get_file(msg.document.file_id)
        file = bot.download_file(file_info.file_path)
        bot.reply_to(msg, '❇️ 接收成功，开始验证插件中')
        testPlugin(file)
        my_open = open('conversion/plugins/' + msg.document.file_name, 'w')
        my_open.write(file.decode('utf-8'))
        my_open.close()
        bot.reply_to(msg, '✅ 插件导入成功')
    except Exception as e:
        logging.error(e.__str__())
        bot.reply_to(msg, '❌ 插件验证失败')


@bot.message_handler(commands=['start'])
def startMessage(msg):
    if msg.chat.type == 'private':
        if msg.from_user.username == config['TELEGRAM']['receive']:
            text = msg.text
            entities = msg.entities
            texts = text.split(" ")
            if text == '/start' and len(entities) == 1 and entities[0].type == 'bot_command':
                markup = types.ReplyKeyboardMarkup(row_width=2)
                addTaskButton = types.KeyboardButton('👹 添加任务')
                listTaskButton = types.KeyboardButton('👀 查看任务')
                addPayloadButton = types.KeyboardButton('👹 添加Payload')
                listPayloadButton = types.KeyboardButton('👀 查看Payload')
                notifyButton = types.KeyboardButton('🛠 开启/关闭通知')
                markup.add(addTaskButton, listTaskButton, addPayloadButton, listPayloadButton, notifyButton)
                bot.send_message(msg.chat.id, '开始扫描吧~', reply_markup=markup)
            elif len(texts) > 1 and len(entities) == 1 and entities[0].type == 'bot_command':
                enStr = texts[1]
                try:
                    jsonData = json.loads(base64.b64decode(enStr.encode('utf-8')).decode('utf-8'))
                    if 'func' in jsonData:
                        func = jsonData['func']
                        if func == 'start' and 'taskId' in jsonData:
                            bot.send_message(msg.chat.id, startTask(jsonData['taskId']))
                        elif func == 'stop' and 'taskId' in jsonData:
                            bot.send_message(msg.chat.id, stopTask(jsonData['taskId']))
                        elif func == 'delete' and 'id' in jsonData:
                            bot.send_message(msg.chat.id, delete_task(jsonData['id']))
                        elif func == 'hit' and 'id' in jsonData:
                            hitStr = hitList(jsonData['id']).split("\n\n")
                            end = 0
                            while len(hitStr) - 1 != end:
                                tempSend = []
                                for i in range(0, 19):
                                    if len(hitStr) - 1 == end:
                                        break
                                    else:
                                        tempSend.append(hitStr[end])
                                    end += 1
                                bot.send_message(msg.chat.id, "\n\n".join(tempSend), parse_mode='Markdown')


                        else:
                            bot.send_message(msg.chat.id, '❌ 指令错误')
                    else:
                        bot.send_message(msg.chat.id, '❌ 指令错误')
                except Exception as e:
                    logging.error('start 指令错误:%s' % e.__str__())
                    bot.send_message(msg.chat.id, '❌指令错误')

        else:
            bot.send_message(msg.chat.id, '⚠️您没有权限使用此服务哦')


# @bot.message_handler(content_types=['file'])
# def file(msg):
#     print('msg:', msg)

@bot.message_handler()
def message(msg):
    if msg.chat.type == 'private':
        if msg.text == '👹 添加任务':
            bot.send_message(msg.chat.id,
                             '字段说明:\n' + '<strong>query</strong> # 查询条件\n'
                                         '<strong>startPage</strong> # 开始页\n'
                                         '<strong>endPage</strong> # 结束页\n'
                                         '<strong>type</strong> # polling 一直轮询/once 只查一次\n'
                                         '<strong>cycle</strong> # 如果为轮询那么间隔的秒数\n'
                                         '<strong>pollingPage</strong> # 如果轮询第二次的结束页\n'
                                         '<strong>openUrl</strong> # 0/1 是否打开详细页进行查找\n\n 实例:\n' +
                             '<code>' + json.dumps(addTaskJson, indent=1) + '</code>', parse_mode="HTML")
        elif msg.text == '👀 查看任务':
            bot.send_message(msg.chat.id, taskList(), parse_mode="Markdown")
        elif msg.text == '👹 添加Payload':
            j = json.dumps(addPayloadJson, indent=1)
            bot.send_message(msg.chat.id,
                             '请求实例:\n' +
                             '<code>' + j + '</code>',
                             parse_mode="HTML")
        elif msg.text == '👀 查看Payload':
            bot.send_message(msg.chat.id, payloadList(), parse_mode="Markdown")
        elif msg.text == '🛠 开启/关闭通知':
            bot.send_message(msg.chat.id, notify(msg.chat.id), parse_mode="Markdown")
        elif msg.text.startswith('code'):
            github.Github().queue.put(msg.text)
        else:
            try:
                j = json.loads(msg.text)
                func = j['func']
                if func == 'addTask':
                    bot.send_message(msg.chat.id, addTask(j['data']))
                elif func == 'addPayload':
                    bot.send_message(msg.chat.id, addPayload(j['data']))
            except Exception as e:
                logging.error('指令异常:%s' % e.__str__())
                bot.send_message(msg.chat.id, '❌指令错误')


def init():
    try:
        return bot.get_me()
    except Exception as e:
        return None


def run():
    bot.polling(none_stop=True)
