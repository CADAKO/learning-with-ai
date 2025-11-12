import os


class BaseLocators:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME", "testdb")
    DB_USER = os.environ.get("DB_USER", "user")
    DB_PASS = os.environ.get("DB_PASS", "password")


