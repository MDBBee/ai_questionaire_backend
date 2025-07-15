from fastapi import APIRouter, Depends, HTTPException, requests
from sqlalchemy.orm import Session
from ..database.db import (get_challenge_quota, reset_quota_if_needed, create_challenge)
from ..database.models import get_db


router = APIRouter()

router.get("/researcher{message}")
async def researcher():
    pass