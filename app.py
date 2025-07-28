from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .routes import challenge, multi_agents, auth
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# ✅ Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bagent.netlify.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

  
app.include_router(challenge.router, prefix="/api")
app.include_router(multi_agents.router, prefix="/agent")
app.include_router(auth.router)
# app.include_router(webhooks.router, prefix="/webhooks")
