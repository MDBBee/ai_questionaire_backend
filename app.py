from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    allow_origins=["https://bagent.netlify.app", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

  
app.include_router(challenge.router, prefix="/api")
app.include_router(multi_agents.router, prefix="/agent")
app.include_router(auth.router)


# ✅ Mount static files
app.mount("/assets", StaticFiles(directory="frontend-main/dist/assets"), name="assets")

# ✅ Catch-all route for SPA (e.g., React Router or Vue Router)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("frontend-main/dist/index.html")



