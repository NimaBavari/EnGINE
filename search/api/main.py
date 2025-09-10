import re
from typing import Tuple

import redis
import requests
from flask import Flask, Response, jsonify, request

from .algorithms import okapi_bm25
from .constants import MLAPI_BASE_URL, REDIS_RESULTS_CONN_STR
from .custom_exc import DocumentRetrievalError
from .repository import InvIdxDBRepository
from .service_utils import get_recommendations

app = Flask(__name__)

redis_instance = redis.Redis.from_url(REDIS_RESULTS_CONN_STR, decode_responses=True)
repo = InvIdxDBRepository()


@app.route("/search", methods=["GET"])
def search() -> Tuple[Response, int]:
    request_params = request.args.to_dict()
    if not all(elem in ["q"] for elem in request_params.keys()):
        return jsonify({"error": "Malformed query params"}), 400

    query = request_params["q"]
    keywords = re.split(r"[ ,.!?;:$*()]+", query.lower())
    query_sorted = "+".join(sorted(keywords))

    cached_result = redis_instance.get(query_sorted)
    if cached_result is not None:
        return jsonify(cached_result), 200

    response_dict = {}

    client_ip = "".join(part.zfill(3) for part in request.environ.get("HTTP_X_REAL_IP", request.remote_addr).split("."))

    user_profile_id = 0

    resp = requests.get("%s//user_profiles/%s" % (MLAPI_BASE_URL, client_ip))
    if resp.status_code == 404:
        resp = requests.post("%s/user_profiles/" % MLAPI_BASE_URL, json={"ip": client_ip})
        if resp.ok:
            user_profile_id = resp.json()["id"]
    elif resp.status_code == 200:
        user_profile_id = resp.json()["user_profile"]["id"]

    recommendations = None
    if user_profile_id:
        resp = requests.post(
            "%s/search_queries/" % MLAPI_BASE_URL, json={"user_profile_id": user_profile_id, "query": query}
        )

        search_query_id = resp.json()["id"]
        response_dict["search_query_id"] = search_query_id
        model = redis_instance.get(user_profile_id)
        recommendations = get_recommendations(model["dataframe"], model["vectorizer"], query)

    try:
        documents, avgdl, keyword_stats = repo.get_documents(keywords)
    except DocumentRetrievalError as e:
        return jsonify({"error": "Something went wrong while fetching results.", "details": str(e)}), 500

    for doc in documents.values():
        kw_aggregate_data = [
            {"keyword": w, "f": keyword_stats[w]["freqs"].get(doc["id"], 0), "idf": keyword_stats[w]["idf"]}
            for w in keywords
        ]
        doc["score"] = okapi_bm25(doc["content"], kw_aggregate_data, avgdl)

    for rec in recommendations:
        if rec in documents:
            documents[rec]["score"] = 1
        else:
            try:
                rec_content = repo.get_document_content(rec)
                documents[rec] = {"id": rec, "content": rec_content, "url": rec, "score": 1}
            except DocumentRetrievalError:
                continue

    ranked_documents = sorted(documents.values(), key=lambda doc: doc["score"], reverse=True)
    response_dict["pages"] = ranked_documents
    redis_instance.set(query_sorted, ranked_documents)

    return jsonify(response_dict), 200
