import math
from typing import Any, Dict, List, Tuple

import elasticsearch

from .constants import ES_CONN_STR, ES_INDEX, ES_RESULTS_SIZE
from .custom_exc import DocumentRetrievalError


class InvIdxDBRepository:
    def __init__(self) -> None:
        self.es = elasticsearch.Elasticsearch(ES_CONN_STR)

    def fetch_keyword_data(self, keyword: str) -> List[Dict[str, Any]]:
        response = self.es.search(
            index=ES_INDEX,
            body={
                "query": {"match": {"content": keyword}},
                "size": ES_RESULTS_SIZE,
                "_source": ["frequency", "doc_length"],
            },
        )

        return [
            {
                "document_id": hit["_id"],
                "frequency": hit["_source"]["frequency"],
                "doc_length": hit["_source"]["doc_length"],
            }
            for hit in response["hits"]["hits"]
        ]

    def get_document_content(self, document_id: str) -> str:
        response = self.es.get(index=ES_INDEX, id=document_id)
        return response["_source"]["content"]

    def get_documents(self, keywords: List[str]) -> Tuple[Dict[str, Dict[str, str]], float, Dict[str, Dict[str, Any]]]:
        documents = {}
        keyword_stats = {kw: {"idf": None, "doc_freq": 0, "freqs": {}} for kw in keywords}
        total_length = 0
        num_docs = 0

        for keyword in keywords:
            try:
                results = self.fetch_keyword_data(keyword)
            except (elasticsearch.ConnectionError, elasticsearch.TransportError):
                raise DocumentRetrievalError

            for result in results:
                doc_id = result["document_id"]
                freq = result["frequency"]
                doc_length = result["doc_length"]
                total_length += doc_length

                if doc_id not in keyword_stats[keyword]["freqs"]:
                    keyword_stats[keyword]["freqs"][doc_id] = freq
                else:
                    keyword_stats[keyword]["freqs"][doc_id] += freq

                keyword_stats[keyword]["doc_freq"] += 1
                if doc_id not in documents:
                    try:
                        documents[doc_id] = {"id": doc_id, "content": self.get_document_content(doc_id), "url": doc_id}
                    except (elasticsearch.ConnectionError, elasticsearch.NotFoundError, elasticsearch.TransportError):
                        raise DocumentRetrievalError

                    num_docs += 1

        avgdl = total_length / num_docs if num_docs > 0 else 0
        for stats in keyword_stats.values():
            if num_docs > 0 and stats["doc_freq"] > 0:
                stats["idf"] = math.log((num_docs - stats["doc_freq"] + 0.5) / (stats["doc_freq"] + 0.5))

        return documents, avgdl, keyword_stats
