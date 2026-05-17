import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

USERS_COLLECTION = os.getenv("USERS_COLLECTION")
STICKERS_COLLECTION = os.getenv("STICKERS_COLLECTION")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db[USERS_COLLECTION]
stickers_collection = db[STICKERS_COLLECTION]

stickers_collection.create_index(
    "created_at",
    expireAfterSeconds=60 * 60 * 24 * 30  
)