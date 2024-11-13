import os

import psycopg2

MLAPI_DB_SCM = """create table if not exists user_profiles(
    id serial,
    ip varchar(15) not null,
    info jsonb,
    primary key (id),
    unique (ip)
);

create table if not exists search_queries(
    id serial,
    user_profile_id int,
    body text not null,
    visited_urls text[],
    primary key (id),
    constraint fk_user_profile foreign key (user_profile_id) references user_profiles (id)
);
"""


def get_postgres_connection() -> psycopg2.extensions.connection:
    postgres_conn_str = os.getenv("POSTGRES_URI", "postgresql://user:secret@localhost:5432/dbname")
    try:
        conn = psycopg2.connect(postgres_conn_str)
    except psycopg2.OperationalError:
        raise
    return conn
