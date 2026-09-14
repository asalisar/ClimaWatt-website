import os

import pymysql


def get_connection():
    return pymysql.connect(
        charset="utf8mb4",
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        connect_timeout=10,
        read_timeout=120,
        write_timeout=120,
        cursorclass=pymysql.cursors.DictCursor,
    )


def execute_query(query, params=None):
    """Esegue una query e restituisce tutte le righe."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    finally:
        connection.close()


def execute_single_query(query, params=None):
    """Esegue una query e restituisce una singola riga."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    finally:
        connection.close()
