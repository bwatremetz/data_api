# Gunicorn serves this app on port 8080
# Nginx picks up and serves on port 8000 (see nginx configuration)

from multiprocessing import cpu_count

# Socket Path
bind = '0.0.0.0:8080'

# Worker Options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = '/var/www/log/data_api/access_log'
errorlog =  '/var/www/log/data_api/error_log'
