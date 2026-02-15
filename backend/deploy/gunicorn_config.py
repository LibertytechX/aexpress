# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 3  # 3 seconds timeout as requested
keepalive = 2

# Logging
accesslog = "/home/backend/logs/gunicorn_access.log"
errorlog = "/home/backend/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "ax_merchant_api"

# Server mechanics
daemon = False
pidfile = "/home/backend/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Nginx)
# keyfile = None
# certfile = None

