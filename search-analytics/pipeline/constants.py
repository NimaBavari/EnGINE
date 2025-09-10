import os

MLAPI_BASE_URL = os.getenv("MLAPI_BASE_URL")
PIPELINE_RUN_PERIOD = int(os.getenv("PIPELINE_RUN_PERIOD", "300"))
REDIS_RESULTS_CONN_STR = os.getenv("REDIS_RESULTS_CONN_STR", "redis://localhost:6379/0")
