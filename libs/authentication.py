import datetime

from jose import jwt
from sqlalchemy import select

from apps.dash.models import Users
from libs.conf import get_session
from libs.const import JwtAuth


def create_token(payload, delta=datetime.timedelta(days=10)):
    claims = payload.copy()
    expire = datetime.datetime.utcnow() + delta
    # 添加失效时间
    claims.update({"exp": expire})
    token = jwt.encode(claims, JwtAuth.SECRET_KEY, algorithm=JwtAuth.ALGORITHM)
    return token


def verify_token(token):
    """
    验证token
    :param token:
    :return: 返回用户信息
    """
    user = None
    try:
        token = token.removeprefix(JwtAuth.HEADER_PREFIX)
        payload = jwt.decode(token, JwtAuth.SECRET_KEY, algorithms=JwtAuth.ALGORITHM)
        username = payload['username']
        query = select(Users).filter_by(username=username)
        session = get_session()
        with session() as db:
            user = db.execute(query).scalar()
    except Exception as e:
        print(e)
        pass
    return user
