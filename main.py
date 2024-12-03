import socketio
import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse

from libs.conf import sio
from urls import router

fast_app = FastAPI()
fast_app.include_router(router, prefix='/api')


app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=fast_app
)
fast_app.mount('/ws', app)

if __name__ == '__main__':
    port = 4088
    uvicorn.run('main:app', host='0.0.0.0', port=port)
