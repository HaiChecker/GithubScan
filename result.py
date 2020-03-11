from flask import jsonify


def result(data, message, code):
    return jsonify({'data': data, 'msg': message, 'code': code})


def success(data):
    return result(data, 'Successful', 200)


def successMsg(msg):
    return result(None, msg, 200)


def fail(msg):
    return result(None, msg, 201)
