import os

ES_CONN_STR = os.getenv("ES_CONN_STR", "https://localhost:9200")
ES_INDEX = ""  # TODO: Set index.

REDIS_CRAWLER_CONN_STR = os.getenv("REDIS_CRAWLER_CONN_STR", "redis://localhost:6379/0")
EXPIRES_AFTER = 86_400
MAX_WORKERS = 10_000
VALIDATOR_PERIOD = 0  # TODO: Set this accordingly.
