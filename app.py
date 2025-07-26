from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .routes import challenge, multi_agents, auth
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bagent.netlify.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(challenge.router, prefix="/api")
app.include_router(multi_agents.router, prefix="/agent")
app.include_router(auth.router)
# app.include_router(webhooks.router, prefix="/webhooks")
