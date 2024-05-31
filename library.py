import sqlite3
from passlib.hash import sha256_crypt

hasher = sha256_crypt.using(rounds=30000)

class DatabaseWorker:
    def __init__(self, name):
        self.name_db = name

    def make_hash(self, text: str):
        return hasher.hash(text)

    def check_hash(self, text: str, hashed: str):
        return hasher.verify(text, hashed)

    def run_query(self, query):
        with sqlite3.connect(self.name_db) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()

    def insert(self, query):
        self.run_query(query)

    def search(self, query, multiple=False):
        with sqlite3.connect(self.name_db) as connection:
            cursor = connection.cursor()
            results = cursor.execute(query)
            if multiple:
                return results.fetchall()
            return results.fetchone()