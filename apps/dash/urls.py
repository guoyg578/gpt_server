from fastapi import APIRouter

from apps.dash.views import login, upload

dashRouter = APIRouter()

dashRouter.add_api_route('/login', login, methods=['post'], tags=['登录'], summary='登录')
dashRouter.add_api_route('/upload', upload, methods=['post'], tags=['文件上传'], summary='文件上传')
