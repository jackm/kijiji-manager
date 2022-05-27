import multiprocessing
import os

workers_per_core_str = os.getenv("WORKERS_PER_CORE", "2")
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "80")

cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
web_concurrency = int(workers_per_core * cores)

# Gunicorn config variables
workers = web_concurrency
bind = f"{host}:{port}"
keepalive = 120
timeout = 120
