import base64
import configparser
import json
import threading

import requests
from sqlalchemy.orm import sessionmaker
from telebot import apihelper
from telebot import types

import telebot

from conversion import conversion
from db import models
from db.models import HConfig

config = configparser.ConfigParser()
config.read('config.ini')

apihelper.proxy = {'https': config['WEB']['proxy']}

bot = telebot.TeleBot(config['TELEGRAM']['token'], threaded=False)

addTaskJson = json.loads(
    '{"query":"eos wallet","startPage":1,"endPage":100,"type":"polling","cycle":3600,"pollingPage":6,"run":true,'
    '"openUrl":1,"payloads":[1,2,3]}')

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

            hitStr = '[没有命中]' if t['hit'] == 0 else '[命中列表](http://t.me/GitHubScanBot?start=%s)' % hitPairStr

            resultStr.append('%s %s %s 命中:%s个 %s' % (t['query'], '🟢' if t['isRun'] else '🔴',
                                                     ('[停止]' if t[
                                                         'isRun'] else '[开始]') + '(http://t.me/GitHubScanBot?start=%s)' % pairStr,
                                                     t['hit'], hitStr))
        return "\n".join(resultStr) if len(resultStr) > 0 else '❌ 您没有任务哦'
    else:
        return tasksJson['msg']


def sendNotify(hit):
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()

    chat = session.query(HConfig).filter(HConfig.k == 'chat_id').one()

    if chat.v != 0:
        result = conversion.hit(hit)
        if result is not None:
            bot.send_message(chat.v, result)


@bot.message_handler(commands=['start'])
def startMessage(msg):
    print(msg.chat.id)
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
                    print(e.__str__())
                    bot.send_message(msg.chat.id, '❌指令错误')

        else:
            bot.send_message(msg.chat.id, '⚠️您没有权限使用此服务哦')


@bot.message_handler()
def message(msg):
    if msg.chat.type == 'private':
        if msg.text == '👹 添加任务':
            bot.send_message(msg.chat.id,
                             '字段说明:\n' + 'query # 查询条件\nstartPage # 开始页\nendPage # 结束页\ntype # polling '
                                         '一直轮询/once 只查一次\ncycle # 如果为轮询那么间隔的秒数\npollingPage # '
                                         '如果轮询第二次的结束页\nopenUrl # 0/1 是否打开详细页进行查找\n\n 实例:\n' +
                             json.dumps(addTaskJson, indent=1))
        elif msg.text == '👀 查看任务':
            bot.send_message(msg.chat.id, taskList(), parse_mode="Markdown")
        elif msg.text == '👹 添加Payload':

            pass
        elif msg.text == '👀 查看Payload':
            bot.send_message(msg.chat.id, payloadList(), parse_mode="Markdown")
        elif msg.text == '🛠 开启/关闭通知':
            bot.send_message(msg.chat.id, notify(msg.chat.id), parse_mode="Markdown")
        else:
            bot.send_message(msg.chat.id, '❌指令错误')


def init():
    try:
        return bot.get_me()
    except Exception as e:
        return None


thread = threading.Thread(target=bot.polling)


def run():
    thread.start()
