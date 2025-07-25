from fastapi import APIRouter, status, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel
from ..database.models import User, db_dependency
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from enum import Enum
import os
from dotenv import load_dotenv
from ..social_credeentials.google_oauth import oauth

    
load_dotenv()   

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY=os.getenv("AUTH_SECRET_KEY")
ALGORITHM=os.getenv("AUTH_ALGORITHM")
EXPIRATION=100

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class Provider(str, Enum):
    credential = "credential"
    google = "google"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: str
    password: str

class CreateUser(UserBase):
    pass

class LoginUser(UserBase):
    pass

class GetUser(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    disabled: bool
    role: UserRole
    image: Optional[str] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2PasswordBearer will not retrieve the token from a cookie — it only looks for the token in the Authorization header by default.
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_user_from_db(db: Session, email: str):
    return db.query(User).filter( User.email == email).first()


def authenticate_user(email, password, db: db_dependency):

    user_exists = get_user_from_db(db, email=email)
    
  
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials, wrong password or email")
    
    if not pwd_context.verify(password, user_exists.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials, wrong password or email")
    
    return user_exists

def create_access_token(email: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": email, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_active_user(db: db_dependency, request: Request) -> GetUser:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied", headers={"www-Authenticate": "Bearer"})

    token = request.cookies.get("access_token")
    if not token:
        raise error
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        email = payload.get("sub")
        token_data = TokenData(email=email)
    except JWTError:
        raise error
    
    user = get_user_from_db(db, token_data.email)
    if user is None or user.disabled :
        raise error
    
    active_user = GetUser(id=user.id, email=user.email, disabled=user.disabled, role=user.role, image=user.image)

    return active_user

# ACTIVE USER DEPENDENCY
active_user_dependnecy = Annotated[GetUser, Depends(get_current_active_user)]


@router.post("/", status_code=status.HTTP_200_OK)
async def create_user(db: db_dependency,  create_user_request: CreateUser):
    hashed_password = pwd_context.hash(create_user_request.password)
    email = create_user_request.email.lower()

    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(email=email, hashed_password=hashed_password, role=UserRole.USER)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_user = GetUser(id=new_user.id, email=new_user.email, disabled=new_user.disabled, role=new_user.role)

    user = authenticate_user(email=new_user.email.lower(), password=create_user_request.password, db=db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

    token = create_access_token(user.email, user.id, timedelta(minutes=EXPIRATION)) 

  
    response = JSONResponse(status_code=status.HTTP_201_CREATED, content={**new_user.model_dump()})
    response.set_cookie(
        key="access_token",
        value=token,
        secure=False,
        httponly=True,
        samesite="lax",
        max_age= 3600 * 100
    )
    return response

@router.post("/logout")
async def logout():

    response = JSONResponse(content={"message":"Logout successful"}, status_code=status.HTTP_200_OK)
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=False,
        samesite="lax"
        )
    return response

@router.post("/token", response_model=Token)
async def login(login_data: LoginUser, db: db_dependency ):

 
    user = authenticate_user(email=login_data.email.lower(), password=login_data.password, db=db)


    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

    token = create_access_token(user.email, user.id, timedelta(minutes=EXPIRATION))  
   
    response = JSONResponse(status_code=status.HTTP_200_OK, content={       "username":user.username,
            "email": user.email,
            "image": user.image,
            "role": user.role,
            "disabled": user.disabled,})
    
    response.set_cookie(
        key="access_token",
        value=token,
        secure=False,
        httponly=True,
        samesite="lax",
        max_age=3600 * 100
    )
    return response

@router.get("/user")
async def get_users(current_user: active_user_dependnecy):

    return current_user


@router.get("/google/login")
async def login_with_google(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: db_dependency):

    token = await oauth.google.authorize_access_token(request)

  
    id_token = token.get("id_token")
     
    if  not id_token:
        raise HTTPException(status_code=400, detail="No ID token in response. Check scopes.")
    
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from provider")
    
    email = user_info.get("email")
    image = user_info.get("picture")
  
    if not email:
        raise HTTPException(status_code=400, detail="Failed to fetch user email")
    
    user = get_user_from_db(db, email=email)

    if not user:
        user = User(email=email, provider=Provider.google, role=UserRole.USER, image=image)
        db.add(user)
        db.commit()
        db.refresh(user)    

    token = create_access_token(user.email, user.id, timedelta(minutes=EXPIRATION))

    # Extract 'next' query param or fallback to "/"
    # next_url = request.query_params.get("next", "/")  
    # Set the JWT as a secure HTTP-only cookie
    response = RedirectResponse(url="http://localhost:5173/agentQ", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # set to True in production with HTTPS
        samesite="Lax",  # or "Strict"
        max_age=3600 * 100
    )
    return response

