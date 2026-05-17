import jwt
from datetime import datetime, timedelta
from fastapi import Header, Cookie, HTTPException 
from bson import ObjectId

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

USERS_COLLECTION = os.getenv("USERS_COLLECTION")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db[USERS_COLLECTION]


def create_access_token(user_id):
    return jwt.encode({
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }, SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id):
    return jwt.encode({
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None

def get_current_user(access_token: str = Cookie(None)):

    if not access_token:
        raise HTTPException(status_code=401, detail="Missing token")

    decoded = decode_token(access_token)

    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = decoded.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        print("SEARCHING USER ID:", user_id)

        # safer ObjectId handling
        try:
            query_id = ObjectId(user_id)
        except Exception:
            query_id = user_id  # fallback if stored as string in DB

        user = users_collection.find_one({"_id": query_id})

        print("FOUND USER:", user)

    except Exception as e:
        print("DATABASE ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Database error")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email")
    }