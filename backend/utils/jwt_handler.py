import jwt
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Request
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


# -------------------------
# CREATE ACCESS TOKEN ONLY
# -------------------------
def create_access_token(user_id):
    print("SECRET_KEY =", SECRET_KEY)
    return jwt.encode({
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")



# -------------------------
# DECODE TOKEN
# -------------------------
def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        print("TOKEN EXPIRED")
        return None

    except jwt.InvalidTokenError as e:
        print("INVALID TOKEN:", str(e))
        return None


# -------------------------
# GET CURRENT USER (AUTH MIDDLEWARE)
# -------------------------
def get_current_user(request: Request):
    authorization = request.headers.get("authorization")
    print("DEBUG RECEIVED HEADER:", authorization)  # <-- Check what the frontend is actually sending!

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth format")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_token(token)
    print("DEBUG DECODED PAYLOAD:", decoded)        # <-- Check if decoding actually returns the JSON object!

    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = decoded.get("user_id")
    print("DEBUG LOOKING UP USER ID:", user_id)

    # Let's see if MongoDB actually finds it
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    print("DEBUG MONGO RESULT:", user)              # <-- If this prints 'None', your DB collection is mismatched or empty!

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"id": str(user["_id"]), "name": user.get("name"), "email": user.get("email")}