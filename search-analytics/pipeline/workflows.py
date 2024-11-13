from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .constants import MLAPI_BASE_URL
from .custom_exc import SearchQueriesNotFetched


def get_user_profiles() -> List[Tuple[Any, ...]]:
    resp = requests.get("%s/user_profiles/" % MLAPI_BASE_URL)
    if resp.status_code != 200:
        raise SearchQueriesNotFetched

    return resp.json()["user_profiles"]


def convert_to_flattened_search_queries_dataframe(queries: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = [{"search_query": entry["body"], "visited_url": url} for entry in queries for url in entry["visited_urls"]]
    return pd.DataFrame(rows)


def train_model(
    data: List[Dict[str, Any]], vectorizer: TfidfVectorizer
) -> Tuple[pd.DataFrame, TfidfVectorizer, np.ndarray]:
    df = convert_to_flattened_search_queries_dataframe(data)
    query_vectors = vectorizer.fit_transform(df["search_query"])
    similarity_matrix = cosine_similarity(query_vectors)

    return df, vectorizer, similarity_matrix
