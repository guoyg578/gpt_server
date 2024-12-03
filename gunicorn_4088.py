import sys
import os
import multiprocessing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 绑定的ip与端口
bind = "0.0.0.0:4088"

# 以守护进程的形式后台运行
daemon = True

# 最大挂起的连接数，64-2048
backlog = 512

# 超时
timeout = 60

# 调试状态
debug = False

# gunicorn要切换到的目的工作目录
chdir = BASE_DIR

# 工作进程类型(默认的是 sync 模式，还包括 eventlet, gevent, or tornado, gthread, gaiohttp)
worker_class = 'uvicorn.workers.UvicornWorker'

# 工作进程数
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 8

# 指定每个工作进程开启的线程数
# threads = multiprocessing.cpu_count()
threads = 1

# 日志级别，这个日志级别指的是错误日志的级别(debug、info、warning、error、critical)，而访问日志的级别无法设置
loglevel = 'error'

# 日志格式
access_log_format = '%(t)s %(r)s %(s)s %(L)s'
# 其每个选项的含义如下：
'''
h          remote address
l          '-'
u          currently '-', may be user name in future releases
t          date of the request
r          status line (e.g. ``GET / HTTP/1.1``)
s          status
b          response length or '-'
f          referer
a          user agent
T          request time in seconds
D          request time in microseconds
L          request time in decimal seconds
p          process ID
'''

# 访问日志文件
accesslog = os.path.join(BASE_DIR, 'access.log')
# 错误日志文件
errorlog = os.path.join(BASE_DIR, 'error.log')
# pid 文件
# pidfile = os.path.join(BASE_DIR, 'gunicorn.pid')

# 访问日志文件，"-" 表示标准输出
# accesslog = "-"
# 错误日志文件，"-" 表示标准输出
# errorlog = "-"

# 进程名
proc_name = 'yolov5'
pythonpath = '/usr/local/python399/bin/python3'

# 更多配置请执行：gunicorn -h 进行查看
