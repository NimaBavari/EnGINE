import os

MLAPI_BASE_URL = os.getenv("MLAPI_BASE_URL")

K = 1.6

ES_CONN_STR = os.getenv("ES_CONN_STR", "https://localhost:9200")
ES_INDEX = "web_pages"
ES_RESULTS_SIZE = 1000

REDIS_RESULTS_CONN_STR = os.getenv("REDIS_RESULTS_CONN_STR", "redis://localhost:6379/0")
