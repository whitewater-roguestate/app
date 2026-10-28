from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
import os
from services import sheets
from fastapi.concurrency import run_in_threadpool
import logging


logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str
    
    
    
@router.get("/login-page-init")
async def initialize_login_screen(request: Request, background_tasks: BackgroundTasks):
    try:
        request.app.state.prefetch_ready.clear()
        # Signal the sheets service to spin up background threads for all sheets
        SPREADSHEET_KEY = "1pI007JsK5eiZD91V77IhkXfAZ7gDiZ7ShfVOI9Jg7ZM"
        
        
        async def run_prefetch_and_unlock():
            try:
                logger.info("Background thread pool task started for sheets prefetch.")
                # Run the heavy synchronous Google Sheets code in the threadpool
                await run_in_threadpool(sheets.start_global_prefetch, SPREADSHEET_KEY)
            except Exception as e:
                logger.error(f"Prefetch worker encountered an error: {e}")
            finally:
                request.app.state.prefetch_ready.set()
                logger.info("Prefetch complete. Gate unlocked, dependent endpoints released.")
        background_tasks.add_task(run_prefetch_and_unlock)
        
        return {"message": "Global data layer validation sequence launched."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        


@router.post("")
def login(data: LoginRequest):
    USERNAME = os.getenv("WWRS_USER")
    PASSWORD = os.getenv("WWRS_PASS")
    if data.username.lower() == USERNAME and data.password.lower() == PASSWORD:
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
