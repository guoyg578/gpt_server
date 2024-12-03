import datetime
from jose.constants import ALGORITHMS


class JwtAuth:
    LOGIN_DELTA = datetime.timedelta(days=3)
    HEADER_PREFIX = 'Bearer '
    ALGORITHM = ALGORITHMS.HS256
    SECRET_KEY = 'django-insecure-l%mqno@^^-3+k-@7hh$_98r4nwe*qhv9!0bd6n)h(#vv=date2'


class Resp:
    @classmethod
    def res_bad(cls, code=400, message='error'):
        return {'code': code, 'message': message}

    @classmethod
    def res_ok(cls, data=None, message='ok', code=0, ):
        return {'code': code, 'data': data, 'message': message}


class Const:
    namespace = '/dash'
    userArr = []
    dashUserMap = {}
    dataDir = 'data'
