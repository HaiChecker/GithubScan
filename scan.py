import configparser

from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker

import result
import exchange

from flask import Flask, request, current_app

from db import models
from db.models import HTask, HPayload, HTaskPayload, HHit, HConfig
from handler import telegram_api
from handler.handler import Handler
from task import Task

app = Flask(__name__)

# 处理线程开启
handler = Handler()
handler.start()
rExchange = exchange.Exchange()
rExchange.subscribe(handler)


@app.route('/payloadList', methods=['GET'])
def payload_list():
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()
    payloads = session.query(HPayload).all()
    resultData = []
    for p in payloads:
        temp = p.to_dict()
        hit = session.query(HHit).filter(HHit.pid == temp['id']).count()
        temp['hit'] = hit
        resultData.append(temp)

    return result.success(resultData)


@app.route('/addPayload', methods=['POST'])
def add_payload():
    req = request.get_json()
    payloads = []

    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()

    for r in req:
        if 'payload' in r and 'title' in r:
            payload = r['payload']
            title = r['title']
            payloadCount = session.query(HPayload).filter(HPayload.title == title).count()
            if payloadCount <= 0:
                payloads.append(HPayload(payload=payload, title=title))
    if len(payloads) > 0:
        return result.successMsg('添加Payload成功')
    else:
        return result.fail('没有有效Payload被添加')


@app.route('/start', methods=['POST'])
def start():
    taskIds = request.get_json()
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()
    hTasks = session.query(HTask).filter(HTask.id.in_(taskIds)).all()
    for hTask in hTasks:
        if hTask.id not in current_app.tasks:
            print('任务未存在于内存中')
            taskPayload = session.query(HPayload).join(HTaskPayload, HTaskPayload.pid == HPayload.id) \
                .filter(HTaskPayload.tid == hTask.id).all()
            task = Task(hTask, taskPayload, rExchange)
            current_app.tasks[hTask.id] = task
            current_app.taskSendExchange.subscribe(task)
        else:
            print('任务存在于内存中')
        current_app.taskSendExchange.send({'func': 'start', 'taskId': hTask.id})

    return result.successMsg('启动任务成功')


@app.route('/stop', methods=['POST'])
def stop():
    taskIds = request.get_json()
    for taskId in taskIds:
        current_app.taskSendExchange.send({'func': 'stop', 'taskId': taskId})

    return result.successMsg('停止任务成功')


@app.route('/reStart', methods=['POST'])
def re_start():
    stop()
    start()
    return result.successMsg('重启任务成功')


@app.route('/hit', methods=['POST'])
def hit():
    requestJson = request.get_json()

    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(HHit)
    if 'id' in requestJson:
        query = query.filter(or_(HHit.pid == requestJson['id'], HHit.tid == requestJson['id']))
    hits = query.all()
    hit = []
    for h in hits:
        hit.append(h.to_dict())
    return result.success(hit)


@app.route('/notify', methods=['GET'])
def notify():
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()
    chatId = request.args.get('chatId')
    chat = session.query(HConfig).filter(HConfig.k == 'chat_id').one()
    notify = session.query(HConfig).filter(HConfig.k == 'notify').one()
    notify.v = 'Y' if notify.v == 'N' else 'N'
    if notify.v == 'Y':
        chat.v = chatId
    else:
        chat.v = 0
    session.commit()

    return result.successMsg(('关闭' if notify.v == 'N' else '开启') + '通知成功')


@app.route('/taskList', methods=['GET'])
def task_list():
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()
    tasks = session.query(HTask).all()
    resultData = []
    for t in tasks:
        temp = t.to_dict()
        temp['isRun'] = False
        hit = session.query(HHit).filter(HHit.tid == temp['id']).count()
        temp['hit'] = hit
        if temp['id'] in current_app.tasks:
            temp['isRun'] = current_app.tasks[temp['id']]._running
        resultData.append(temp)

    return result.success(resultData)


# 任务添加
@app.route('/addTask', methods=['POST', 'GET'])
def add_task():
    req = request.get_json()
    query = req['query']
    engine = models.getDb()
    Session = sessionmaker(bind=engine)
    session = Session()

    taskCount = session.query(HTask).filter(HTask.query == query).count()
    if taskCount > 0:
        return result.fail('添加任务失败，任务已存在')

    taskData = HTask(query=query, state=1, startPage=req['startPage'], endPage=req['endPage'], type=req['type'],
                     cycle=req['cycle'], pollingPage=req['pollingPage'], openUrl=req['openUrl'])
    session.add(taskData)
    taskPayloadIns = []
    taskPayload = []
    if 'payloads' in req and len(req['payloads']) > 0:
        payloads = req['payloads']
        for p in payloads:
            payloadCount = session.query(HPayload).filter(HPayload.id == p).count()
            if payloadCount > 0:
                taskPayloadIns.append(HTaskPayload(pid=int(p), tid=taskData.id))
        if len(taskPayloadIns) > 0:
            session.add_all(taskPayloadIns)
            taskPayload = session.query(HPayload).filter(HPayload.id.in_(payloads)).all()

    session.commit()

    t = Task(taskData, taskPayload, rExchange)
    current_app.tasks[taskData.id] = t
    current_app.taskSendExchange.subscribe(t)

    if req['run']:
        t.start()

    return result.success('添加任务:%s 成功' % taskData.query)


if __name__ == '__main__':
    print('启动Github扫描啦')
    config = configparser.ConfigParser()
    config.read('config.ini')
    port = config['WEB']['port']
    host = config['WEB']['host']

    if config['TELEGRAM']['token']:
        telegramResult = telegram_api.init()
        if telegramResult:
            print('Telegram 启动成功，开始监听')
            telegram_api.run()

        else:
            print('Telegram 启动失败')

    ctx = app.app_context()
    ctx.push()
    current_app.tasks = {}
    current_app.taskSendExchange = exchange.Exchange()
    current_app.taskReceiveExchange = exchange.Exchange()

    app.run(host=host, port=port, use_reloader=False)
