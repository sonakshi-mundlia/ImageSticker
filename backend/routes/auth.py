from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from db.mongo import users_collection
from utils.jwt_handler import create_access_token, create_refresh_token, decode_token, get_current_user
import bcrypt

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenRequest(BaseModel):
    refresh_token: str

router = APIRouter()

@router.post("/register")
def register(data: RegisterRequest):

    existing_user = users_collection.find_one({
        "email": data.email
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    hashed_pw = bcrypt.hashpw(
        data.password.encode(),
        bcrypt.gensalt()
    ).decode("utf-8")

    users_collection.insert_one({
        "name": data.name,
        "email": data.email,
        "password": hashed_pw
    })

    return {
        "message": "User registered successfully"
    }


@router.post("/login")
def login(data: LoginRequest, response: Response):

    user = users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(data.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = str(user["_id"])

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

     # Secure cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False  # True when using HTTPS
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False  # True in production HTTPS
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.get("/profile")
def profile(user=Depends(get_current_user)):

    return {
        "email": user["email"],
        "name": user.get("name", "")
    }

