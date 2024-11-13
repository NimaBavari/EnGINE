from typing import Any, Dict, List, Tuple

from flask import Flask, request

from .custom_exc import FetchError, InsertionError, NotFoundError
from .repository import PostgresMLAPIRepository

app = Flask(__name__)

repo = PostgresMLAPIRepository()


@app.route("/user_profiles/", methods=["POST"])
def create_user_profile() -> Tuple[Dict[str, Any], int]:
    """Incoming request shape:
    ```json
    {
        "ip":   IP of the user, string
        "info": optional; other profile info, dict
    }
    ```
    """
    try:
        ip = request.json["ip"]
    except KeyError:
        return {"status": "Malformed request: missing IP."}, 400
    info = request.json.get("info", {})
    try:
        user_profile_id = repo.insert_user_profile(ip, info)
    except InsertionError:
        return {"status": "Error inserting user profile."}, 500
    return {"id": user_profile_id}, 201


@app.route("/user_profiles/<user_ip>/", methods=["GET"])
def get_user_profile(user_ip: str) -> Tuple[Dict[str, Any], int]:
    try:
        user_profile_dict = repo.fetch_user_profile(user_ip)
    except FetchError:
        return {"status": "Error fetching user profile."}, 500
    except NotFoundError:
        return {"status": "User profile not found."}, 404
    return {"user_profile": user_profile_dict}, 200


@app.route("/user_profiles/", methods=["GET"])
def get_user_profiles() -> Tuple[Dict[str, List[Any]], int]:
    try:
        user_profiles = repo.fetch_user_profiles()
    except FetchError:
        return {"status": "Error fetching user profiles."}, 500
    return {"user_profiles": user_profiles}, 200


@app.route("/search_queries/", methods=["POST"])
def create_search_query() -> Tuple[Dict[str, Any], int]:
    """Incoming request shape:
    ```json
    {
        "user_profile_id":  user profile id, int
        "query":            search query, string
        "visited_urls":     optional; visited urls, list
    }
    ```
    """
    try:
        user_profile_id = request.json["user_profile_id"]
        query = request.json["query"]
    except KeyError:
        return {"status": "Malformed request: missing fields."}, 400
    visited_urls = request.json.get("visited_urls", [])
    try:
        search_query_id = repo.insert_search_query(user_profile_id, query, visited_urls)
    except InsertionError:
        return {"status": "Error inserting search query."}, 500
    return {"id": search_query_id}, 201


@app.route("/search-queries/<int:search_query_id>/", methods=["GET"])
def get_search_query(search_query_id: int) -> Tuple[Dict[str, Any], int]:
    try:
        search_query_dict = repo.fetch_search_query(search_query_id)
    except FetchError:
        return {"status": "Error fetching search query."}, 500
    except NotFoundError:
        return {"status": "Search query not found."}, 404
    return {"search_query_dict": search_query_dict}, 200


@app.route("/search-queries/<int:search_query_id>/visited-urls/", methods=["PATCH"])
def add_visited_url(search_query_id: int) -> Tuple[Dict[str, Any], int]:
    """Incoming request shape:
    ```json
    {
        "url":  URL to append, string
    }
    ```
    """
    try:
        new_url = request.json["url"]
    except KeyError:
        return {"status": "Malformed request: missing URL."}, 400
    try:
        repo.append_visited_url(search_query_id, new_url)
    except InsertionError:
        return {"status": "Error appending URL."}, 500
    return {"status": "URL appended successfully."}, 204
