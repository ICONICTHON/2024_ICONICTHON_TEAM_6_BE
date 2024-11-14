from pymongo import MongoClient
from dotenv import load_dotenv
import os

def def_client():
    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    print(uri)
    client = MongoClient(uri)
    return client

def server_info():
    try:
        client = def_client()
        return client.server_info()
    except Exception as err:
        print(err)

def get_collection(collection:str):
    client = def_client()
    database = client.get_database(os.environ.get("MONGO_DATABASE"))
    collection = database.get_collection(collection)
    return collection

def quick(collection:str, query:dict) -> list:
    try:
        client = def_client()
        database = client.get_database(os.environ.get("MONGO_DATABASE"))
        collection = database.get_collection(collection)
        items = collection.find(query)
        client.close()
        return items
    except Exception as e:
        raise Exception("Unable to find the document due to the following error: ", e)
