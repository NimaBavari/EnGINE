from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import precision_score, recall_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split


def get_recommendations(df: pd.DataFrame, vectorizer: TfidfVectorizer, new_query: str, top_n: int = 5) -> List[str]:
    query_vectors = vectorizer.fit_transform(df["search_query"])

    new_query_vector = vectorizer.transform([new_query])
    similarity_scores = cosine_similarity(new_query_vector, query_vectors).flatten()
    similar_indices = similarity_scores.argsort()[-top_n:][::-1]

    recommended_urls = []
    for idx in similar_indices:
        query = df.iloc[idx]["search_query"]
        urls = df[df["search_query"] == query]["visited_url"].tolist()
        recommended_urls.extend(urls)

    return list(set(recommended_urls))[:top_n]


def evaluate_recommender(
    df: pd.DataFrame, vectorizer: TfidfVectorizer, similarity_matrix: np.ndarray, top_n: int = 5
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    _, test_data = train_test_split(df, test_size=0.2, random_state=42)
    test_df = pd.DataFrame(
        [
            {"search_query": entry["search_query"], "visited_url": url}
            for entry in test_data
            for url in entry["visited_urls"]
        ]
    )

    y_true = []
    y_pred = []
    for query in test_df["search_query"].unique():
        true_urls = test_df[test_df["search_query"] == query]["visited_url"].tolist()
        recommended_urls = get_recommendations(query, df, vectorizer, similarity_matrix, top_n)
        y_true.extend([1] * len(true_urls))
        y_pred.extend([1 if url in recommended_urls else 0 for url in true_urls])

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)

    return precision, recall
