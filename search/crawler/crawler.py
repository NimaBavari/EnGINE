"""Crawler module.

Features:
    * multi-threaded;
    * persists documents in a key-value store;
    * uses smart caching.
"""
import io
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from gzip import GzipFile
from html.parser import HTMLParser
from typing import List
from urllib.parse import urlparse

import elasticsearch
import redis

from .constants import ES_INDEX, EXPIRES_AFTER, MAX_WORKERS


class URLCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        dict_attrs = dict(attrs)
        if tag == "a" and "href" in dict_attrs:
            self.urls.append(dict_attrs["href"])

    def flush(self) -> List[str]:
        urls = self.urls
        self.urls = []
        return urls


class Crawler:
    def __init__(
        self,
        start_url: str,
        redis_instance: redis.Redis,
        es_instance: elasticsearch.Elasticsearch,
        logger: logging.Logger,
    ) -> None:
        start_long_url = start_url
        if "://" not in start_url:
            start_long_url = "http://%s" % start_long_url

        self.url_collector = URLCollector()

        self.queue = set([start_long_url])
        self.redis = redis_instance
        self.es = es_instance

        self.logger = logger

    def parse_links(self, page: str) -> List[str]:
        self.url_collector.feed(page)
        return self.url_collector.flush()

    def process_single_url(self, url: str) -> None:
        self.logger.info("Attempting to bring %s from cache." % url)

        page = self.redis.get(url)
        if not page:
            self.logger.info("Not found in cache. Starting fetch on %s." % url)
            try:
                resp = urllib.request.urlopen(url)
            except (urllib.error.URLError, ValueError):
                self.logger.info("Fetch failed: putting %s back into the queue." % url)
                self.queue.add(url)
                return

            charset = resp.info().get_content_charset() or "utf-8"
            try:
                page = resp.read().decode(charset)
            except UnicodeDecodeError:
                gzip_file = GzipFile(fileobj=io.BytesIO(resp.read()))
                page = gzip_file.read().decode()

            ttl = EXPIRES_AFTER
            cache_control_parts = resp.headers.get("cache-control", "").split("=")
            if len(cache_control_parts) >= 2:
                try:
                    ttl = int(cache_control_parts[1])
                except ValueError:
                    pass

            try:
                _ = self.es.index(index=ES_INDEX, id=url, document={"content": page})
            except (elasticsearch.ConnectionError, elasticsearch.TransportError):
                self.logger.error("Indexing the document at %s failed." % url)
                return

            self.redis.set(url, page, ex=ttl)
            self.redis.hset("metadata:%s" % url, mapping={"charset": charset, "expires": ttl})

            self.logger.info("Fetched and cached page from %s." % url)
        else:
            self.logger.info("Brought page from %s." % url)

        for link_url in self.parse_links(page):
            try:
                link_long_url = link_url.decode()
            except AttributeError:
                link_long_url = link_url

            link_parse_res = urlparse(link_long_url)
            if not link_parse_res.netloc:
                curr_parse_res = urlparse(url)
                link_long_url = link_parse_res._replace(
                    scheme=curr_parse_res.scheme, netloc=curr_parse_res.hostname
                ).geturl()

            if not (link_parse_res.params or link_long_url.endswith("/")):
                link_long_url += "/"

            if not self.redis.exists(link_long_url):
                self.logger.info("New link detected: %s. Adding to the queue." % link_long_url)
                self.queue.add(link_long_url)

    def run(self) -> None:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as process_ops_exec:
            futures = set()
            while self.queue or futures:
                while self.queue and len(futures) < MAX_WORKERS:
                    current_url = self.queue.pop()
                    future = process_ops_exec.submit(self.process_single_url, current_url)
                    futures.add(future)

                done_futures = {f for f in futures if f.done()}
                futures.difference_update(done_futures)
                for future in done_futures:
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error("Error processing URL: %s" % e)

            self.logger.info("Crawler is done!")
