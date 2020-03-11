# coding: utf-8
import configparser

from sqlalchemy import Column, String, Text, text, create_engine
from sqlalchemy.dialects.mysql import INTEGER, MEDIUMTEXT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class HConfig(Base):
    __tablename__ = 'h_config'

    k = Column(String(255, 'utf8_bin'), primary_key=True)
    v = Column(String(255, 'utf8_bin'), nullable=False)



class HHit(Base):
    __tablename__ = 'h_hit'

    id = Column(INTEGER(11), primary_key=True)
    tid = Column(INTEGER(11), nullable=False, comment='任务ID')
    pid = Column(INTEGER(11), nullable=False, comment='Payload ID')
    url = Column(Text(collation='utf8_bin'), nullable=False, comment='命中的URL地址')
    hit = Column(Text(collation='utf8_bin'), nullable=False, comment='命中的值')
    hitHash = Column(VARCHAR(255), nullable=False, comment='命中的值的Hash')

    # 方式一
    def to_dict(self):
        dict = {}
        dict.update(self.__dict__)
        if "_sa_instance_state" in dict:
            del dict['_sa_instance_state']
        return dict


class HPayload(Base):
    __tablename__ = 'h_payload'

    id = Column(INTEGER(11), primary_key=True, comment='payloaId')
    payload = Column(Text(collation='utf8_bin'), comment='正则匹配（空代表只匹配查询条件）')
    title = Column(VARCHAR(255), nullable=False, comment='说明')

    # 方式一
    def to_dict(self):
        dict = {}
        dict.update(self.__dict__)
        if "_sa_instance_state" in dict:
            del dict['_sa_instance_state']
        return dict


class HTask(Base):
    __tablename__ = 'h_task'

    id = Column(INTEGER(11), primary_key=True, comment='任务ID')
    query = Column(VARCHAR(255), nullable=False, comment='任务查询条件')
    state = Column(INTEGER(10), nullable=False, comment='任务状态')
    startPage = Column(INTEGER(10), nullable=False, comment='开始页')
    endPage = Column(INTEGER(10), nullable=False, comment='结束页')
    type = Column(String(100, 'utf8_bin'), nullable=False, server_default=text("'polling,once'"), comment='任务模式')
    cycle = Column(INTEGER(50), nullable=False, comment='轮询周期（秒）')
    pollingPage = Column(INTEGER(10), nullable=False, comment='当第一次任务结束后每次轮询结束页')
    openUrl = Column(INTEGER(1), nullable=False, default=1, comment='是否打开内页探索')

    # 方式一
    def to_dict(self):
        dict = {}
        dict.update(self.__dict__)
        if "_sa_instance_state" in dict:
            del dict['_sa_instance_state']
        return dict


class HTaskPayload(Base):
    __tablename__ = 'h_task_payload'

    id = Column(INTEGER(11), primary_key=True)
    pid = Column(INTEGER(11), nullable=False)
    tid = Column(INTEGER(11), nullable=False)

    # 方式一
    def to_dict(self):
        dict = {}
        dict.update(self.__dict__)
        if "_sa_instance_state" in dict:
            del dict['_sa_instance_state']
        return dict


def createSqlite(dbName):
    # 初始化数据库连接:
    engine = create_engine('sqlite:///%s.db' % dbName)
    metadata.create_all(engine)
    return engine


def createMysql(userName, userPwd, host, port, dbName):
    # 初始化数据库连接:
    engine = create_engine('mysql+pymysql://%s:%s@%s:%s/%s' % (userName, userPwd, host, port, dbName))
    metadata.create_all(engine)
    return engine


def getDb():
    config = configparser.ConfigParser()
    config.read('config.ini')
    dbType = config['DB']['db']
    if dbType == 'mysql':
        pair = {'dbUser': config['DB']['dbUser'], 'dbUserPwd': config['DB']['dbUserPwd'],
                'dbName': config['DB']['dbName'], 'dbPort': config['DB']['dbPort'],
                'dbHost': config['DB']['dbHost']}
        return createMysql(pair['dbUser'], pair['dbUserPwd'], pair['dbHost'], pair['dbPort'], pair['dbName'])
    else:
        pass
    return None
