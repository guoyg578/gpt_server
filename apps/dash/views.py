import datetime
import random
import sys
from pathlib import Path

import pyodbc
import random_string
from fastapi import UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from apps.dash.models import Users, DashLogsLogin
from libs.authentication import create_token, verify_token
from libs.conf import sio, get_session
from libs.const import Resp, Const

routineConn = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=idc.venndata.cn,30014;DATABASE=Venndash_test;UID=reteller;PWD=567890"

debug = sys.platform == 'win32'


class Item(BaseModel):
    username: str
    password: str


def login(form: Item):
    query = select(Users).filter_by(username=form.username, password=form.password)
    session = get_session()
    with session() as db:
        user = db.execute(query).scalar()
        if user is None:
            return Resp.res_bad('用户名或密码错误！')
        payload = {'username': form.username, 'roleId': user.roleId}
        token = create_token(payload)
        obj = DashLogsLogin(username=user.username, createTime=datetime.datetime.now())
        db.add(obj)
        db.commit()
        res = {'token': token}
    return Resp.res_ok(res, '登陆成功')


async def upload(file: UploadFile = File(...)):
    stat = file.filename.split('.')[-1]
    fileName = random_string.generate(max_length=12, min_length=12) + '.' + stat
    filePath = Path(Const.dataDir, fileName)
    with open(filePath, 'wb') as f:
        content = await file.read()
        f.write(content)
    return filePath


async def stream_text(sid, event, text, role=None):
    client = Const.dashUserMap[sid]
    count = len(text)
    end = 0
    while end < count:
        if not client.get('emit'):
            break
        length = random.choice([1, 2, 3])
        end += length
        text_data = {
            'content': text[: end],

        }
        if role:
            text_data['role'] = role
        await sio.emit(event=event, to=sid, data=text_data, namespace=Const.namespace)
        # await asyncio.sleep(0.03)


@sio.on('text', namespace=Const.namespace)
async def dash_text(sid, body):
    token = body.get('token')
    content = body.get('content')
    # user = verify_token(token)
    # if user is None:
    #     await sio.emit(event='login', to=sid, namespace=Const.namespace)
    #     return

    msg = {'role': 'user',
           'content': content
           }

    await sio.emit(event='user', data=msg, to=sid, namespace=Const.namespace)
    # await asyncio.sleep(3)
    text = (f'系统暂不支持回答您的问题，'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问'
            f'请您更换其他问题进行提问')
    await stream_text(sid, 'assistant', text, role='assistant', )
    await sio.emit(event='end', data=msg, to=sid, namespace=Const.namespace)
    return


@sio.on('stop', namespace=Const.namespace)
def stop_conversation(sid):
    client = Const.dashUserMap.get(sid)
    if client:
        client['emit'] = False


@sio.on('connect', namespace=Const.namespace)
def dash_connect(sid, a, b):
    Const.dashUserMap[sid] = {
        'emit': True,
        'messages': []
    }


@sio.on('disconnect', namespace=Const.namespace)
def dash_disconnect(sid):
    Const.dashUserMap.pop(sid, None)


def get_cate_channel(roleId):
    conn = pyodbc.connect(routineConn, autocommit=True)
    cursor = conn.cursor()
    cateSql = f'''SELECT a.cateLabelCn, b.cateId, b.cateParent, a.cateParentName  FROM dash_catetreemap b 
                                    JOIN dash_catetree c ON (b.cateTreeId= c.cateTreeId) 
                                    JOIN dash_role d ON (c.cateTreeId= d.cateTreeId) 
                                    JOIN dash_cate a ON (b.cateId=a.cateId) 
                                    WHERE (c.flag= 1 AND d.roleId= {roleId} AND d.flag=1 AND a.flag=1 AND b.flag=1) ORDER BY a.sortId ASC'''

    channelSql = f'''SELECT a.channelLabelCn, b.channelId  FROM dash_channeltreemap b 
                                    JOIN dash_channeltree c ON (b.channelTreeId= c.channelTreeId) 
                                    JOIN dash_role d ON (c.channelTreeId= d.channelTreeId) 
                                    JOIN dash_channel a ON (b.channelId=a.channelId) 
                                    WHERE c.flag= 1 AND d.roleId= {roleId} AND d.flag=1 AND a.flag=1 AND b.flag=1'''

    cursor.execute(cateSql)
    cateRow = cursor.fetchall()
    cateMap = {i[0]: list(i) for i in cateRow}

    cursor.execute(channelSql)
    channelRow = cursor.fetchall()
    channelMap = {i[0]: i[1] for i in channelRow}
    return cateMap, channelMap
