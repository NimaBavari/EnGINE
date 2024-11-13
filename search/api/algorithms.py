from typing import Any, Dict, List

from .constants import K


def okapi_bm25(doc_content: str, keyword_aggragate_data: List[Dict[str, Any]], avgdl: float) -> float:
    doc_len = len(doc_content)
    return sum(
        mapping["idf"] * mapping["f"] * (K + 1) / (mapping["f"] + K * (0.25 + 0.75 * doc_len / avgdl))
        for mapping in keyword_aggragate_data
    )
