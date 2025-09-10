# NOTE: The pipeline control flow is controlled by custom exceptions for now.
import json
import time

import redis
from sklearn.feature_extraction.text import TfidfVectorizer

from .constants import PIPELINE_RUN_PERIOD, REDIS_RESULTS_CONN_STR
from .custom_exc import SearchQueriesNotFetched
from .workflows import get_user_profiles, train_model

redis_instance = redis.Redis.from_url(REDIS_RESULTS_CONN_STR, decode_responses=True)

while True:
    start = time.perf_counter()
    try:
        user_profiles = get_user_profiles()
    except SearchQueriesNotFetched as e:
        print("%s" % e, flush=True)
        continue

    for user_profile_id, search_queries in user_profiles:
        # `search_queries` example:
        # [
        #     {
        #         "search_id": 1,
        #         "body": "search 1",
        #         "visited_urls": ["http://example.com", "http://example.org"]
        #     }, {
        #         "search_id": 2,
        #         "body": "search 2",
        #         "visited_urls": ["http://example.net"]
        #     }
        # ]
        if not redis_instance.exists(user_profile_id):
            vectorizer = TfidfVectorizer()
        else:
            vectorizer = json.loads(redis_instance.get(user_profile_id))["vectorizer"]

        df, vectorizer, sim_matrix = train_model(search_queries, vectorizer)
        redis_instance.set(
            user_profile_id,
            json.dumps(
                {
                    "vectorizer": vectorizer.get_params(),
                    "dataframe": df.to_json(),
                    "similarity_matrix": sim_matrix.tolist(),
                }
            ),
        )

    elapsed = time.perf_counter() - start
    print("Analytics pipeline took: %.2f." % elapsed, flush=True)
    time.sleep(PIPELINE_RUN_PERIOD - elapsed)
