from psycopg2.extensions import connection as connection_type
import psycopg2
import os

# Параметры БД
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "te"
                                    "stdb")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASS = os.environ.get("DB_PASS", "password")


def get_db_connection() -> connection_type:
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                            password=DB_PASS)
    return conn
