import json
from utils import *

storage_db = "storage.db"
users_db = "user.db"

def write_to_users(data):
    with open(users_db, "w") as user_desc:
        json.dump(data, user_desc, cls=SetEncoder)

def read_from_users():
    with open(users_db, "r") as user_desc:
        data = json.load(user_desc)
        return data

def write_to_storage(data):
    with open(storage_db, "w") as storage_desc:
        json.dump(data, storage_desc)

def read_from_storage():
    with open(storage_db, "r") as storage_desc:
        data = json.load(storage_desc)
        return data
