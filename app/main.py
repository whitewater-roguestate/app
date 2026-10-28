import os, sys
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from fastapi import APIRouter, Depends, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import groups, login, profiles, trip_log
from services import email, form, sheets, drive
from dotenv import load_dotenv
import logging
import asyncio

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,format="[%(levelname)s] %(name)s: %(message)s")


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow connections from any device (essential for local phone testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"])

load_dotenv()
os.makedirs("./static/trip_photos", exist_ok=True)

#router routers
app.include_router(login.router,prefix="/api/login")
app.include_router(groups.router,prefix="/api/groups")
app.include_router(profiles.router,prefix="/api/paddlers")
app.include_router(trip_log.router,prefix="/api/trip-log")

#services routers
app.include_router(email.router)
app.include_router(form.router, prefix="/api/form")
app.include_router(sheets.router, prefix="/api/sheets")
app.include_router(drive.router, prefix="/api/drive")

app.state.prefetch_ready = asyncio.Event()
app.state.prefetch_ready.set()


@app.get("/")
def read_index():
    return FileResponse("index.html")
