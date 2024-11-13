import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import elasticsearch
import redis

from .constants import ES_INDEX, MAX_WORKERS
from .crawler import Crawler


class CacheValidator:
    def __init__(
        self, redis_instance: redis.Redis, es_instance: elasticsearch.Elasticsearch, logger: logging.Logger
    ) -> None:
        self.redis = redis_instance
        self.es = es_instance
        self.logger = logger

    def is_cache_valid(self, url: str) -> bool:
        metadata = self.redis.hgetall("metadata:%s" % url)
        if not metadata:
            return False

        try:
            header_resp = urllib.request.Request(url, method="HEAD")
            resp = urllib.request.urlopen(header_resp)
            return (
                resp.headers.get("Last-Modified", "") == metadata["last_modified"]
                and resp.headers.get("ETag", "") == metadata["etag"]
            )
        except Exception as e:
            self.logger.error("Failed to validate cache for %s: %s" % (url, e))
            return False

    def invalidate(self, url: bytes) -> str | None:
        real_url = url.decode().split("metadata:")[1]
        if not self.is_cache_valid(real_url):
            try:
                _ = self.es.delete(index=ES_INDEX, id=real_url)
            except (elasticsearch.ConnectionError, elasticsearch.TransportError):
                self.logger.error("Deleting the document at %s failed." % real_url)
                return

            self.redis.delete(real_url)
            self.redis.delete("metadata:%s" % real_url)
            self.logger.info("Cache invalidated for %s." % real_url)

            return real_url

    def run(self) -> None:
        self.logger.info("Validating cache.")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as cache_ops_exec:
            results = cache_ops_exec.map(self.invalidate, self.redis.scan_iter(match="metadata:*"))

        if results:
            Crawler(results[-1], self.redis, self.es, self.logger).run()
