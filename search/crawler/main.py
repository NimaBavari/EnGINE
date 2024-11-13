import logging
import sys

import elasticsearch
import redis

from .caching import CacheValidator
from .constants import ES_CONN_STR, REDIS_CRAWLER_CONN_STR, VALIDATOR_PERIOD
from .crawler import Crawler

if __name__ == "__main__":
    r = redis.Redis.from_url(REDIS_CRAWLER_CONN_STR, decode_responses=True)

    es = elasticsearch.Elasticsearch(ES_CONN_STR)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    # run once
    crawler = Crawler("https://isitchristmas.com/", r, es, logger)

    import time

    run_once_start = time.perf_counter()
    crawler.run()
    once_elapsed = time.perf_counter() - run_once_start
    print("Crawler took: %.2f." % once_elapsed, flush=True)

    # schedule a cache validator run
    elapsed = once_elapsed
    cache_validator = CacheValidator(r, es, logger)
    while True:
        time.sleep(VALIDATOR_PERIOD - elapsed)
        run_start = time.perf_counter()
        cache_validator.run()
        elapsed = time.perf_counter()
