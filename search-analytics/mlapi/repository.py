from typing import Any, Dict, List, Tuple

import psycopg2

from .custom_exc import FetchError, InsertionError, NotFoundError
from .db import MLAPI_DB_SCM, get_postgres_connection


class PostgresMLAPIRepository:
    def __init__(self) -> None:
        self.conn: psycopg2.extensions.connection = get_postgres_connection()
        self.cursor: psycopg2.extensions.cursor = self.conn.cursor()
        self.cursor.execute(MLAPI_DB_SCM)
        self.conn.commit()

    def insert_user_profile(self, ip: str, info: Dict[str, Any]) -> int:
        try:
            self.cursor.execute("insert into user_profiles (ip, info) values (%s, %s) returning id;", (ip, info))
        except psycopg2.Error as e:
            raise InsertionError from e

        (user_profile_id,) = self.cursor.fetchone()
        self.conn.commit()

        return user_profile_id

    def fetch_user_profile(self, user_ip: int) -> Dict[str, Any]:
        try:
            self.cursor.execute(
                """
                select
                    user_profiles.id,
                    user_profiles.ip,
                    user_profiles.info,
                    coalesce(json_agg(json_build_object(
                        'id', search_queries.id,
                        'body', search_queries.body,
                        'visited_urls', search_queries.visited_urls
                    ) order by search_queries.id) filter (where search_queries.id is not null), '[]') queries
                from
                    user_profiles
                left join
                    search_queries ON user_profiles.id = search_queries.user_profile_id
                where
                    user_profiles.ip = %s
                group by
                    user_profiles.id, user_profiles.ip, user_profiles.info;
                """,
                (user_ip,),
            )
        except psycopg2.Error as e:
            raise FetchError from e

        try:
            id_, ip, info, search_queries = self.cursor.fetchone()
        except Exception:
            raise NotFoundError

        return {"id": id_, "ip": ip, "info": info, "search_queries": search_queries}

    def fetch_user_profiles(self) -> List[Tuple[Any, ...]]:
        try:
            self.cursor.execute(
                """
                select
                    user_profiles.id,
                    jsonb_agg(jsonb_build_object(
                        'search_id', search_queries.id,
                        'body', search_queries.body,
                        'visited_urls', search_queries.visited_urls
                    )) as search_queries
                from
                    user_profiles
                inner join
                    search_queries ON user_profiles.id = search_queries.user_profile_id
                group by
                    user_profiles.id
                order by
                    user_profiles.id;
            """
            )
        except psycopg2.Error as e:
            raise FetchError from e

        return self.cursor.fetchall()

    def insert_search_query(self, user_profile_id: int, query: str, visited_urls: List[str]) -> int:
        try:
            self.cursor.execute(
                "insert into search_queries (user_profile_id, body, visited_urls) values (%s, %s, %s) returning id;",
                (user_profile_id, query, visited_urls),
            )
        except psycopg2.Error as e:
            raise InsertionError from e

        (search_query_id,) = self.cursor.fetchone()
        self.conn.commit()

        return search_query_id

    def fetch_search_query(self, search_query_id: int) -> Dict[str, Any]:
        try:
            self.cursor.execute(
                "select * from search_queries where id = %s;",
                search_query_id,
            )
        except psycopg2.Error as e:
            raise FetchError from e

        try:
            id_, user_profile_id, body, visited_urls = self.cursor.fetchone()
        except Exception:
            raise NotFoundError

        return {"id": id_, "user_profile_id": user_profile_id, "body": body, "visited_urls": visited_urls}

    def append_visited_url(self, search_query_id: int, new_url: str) -> None:
        try:
            self.cursor.execute(
                "update search_queries set visited_urls = array_append(visited_urls, %s) where id = %s;",
                (new_url, search_query_id),
            )
        except psycopg2.Error as e:
            raise InsertionError from e

        self.conn.commit()
