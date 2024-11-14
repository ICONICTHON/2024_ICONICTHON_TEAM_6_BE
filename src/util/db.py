import os

from flask.cli import load_dotenv
from pymongo import MongoClient


def def_client():
    load_dotenv()
    uri = os.environ.get("DB_URI")
    client = MongoClient(uri)
    return client


def server_info():
    try:
        client = def_client()
        return client.server_info()
    except Exception as e:
        print(e)


def get_collection(collection: str):
    client = def_client()
    database = client.get_database(os.environ.get("DB_NAME"))
    collection = database.get_collection(collection)
    return collection


def quick(collection: str, query: dict) -> list:
    try:
        client = def_client()
        database = client.get_database(os.environ.get("DB_NAME"))
        collection = database.get_collection(collection)
        items = collection.find(query)
        client.close()
        return items
    except Exception as e:
        raise Exception("Unable to find the document due to the following error: ", e)
