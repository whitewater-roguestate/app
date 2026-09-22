from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from fastapi import APIRouter, Depends, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import gspread
from extra_functions import *
from app_cache import app_cache
from dotenv import load_dotenv, find_dotenv
import os
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import shutil
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request 


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow connections from any device (essential for local phone testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
load_dotenv()
os.makedirs("./static/trip_photos", exist_ok=True)




#SCHEMAS
class LoginRequest(BaseModel):
    username: str
    password: str
    
class GroupRequest(BaseModel):
    group_name: str
    member_names: list[str]

class TripLogSchema:
    def __init__(
        self,
        location: str = Form(...),
        message: str = Form(...),
        members: str | None = Form("Solo"),  # <-- Clean and modern
        photo: UploadFile | None = File(None) # <-- Clean and modern
    ):
        self.location = location
        self.message = message
        self.members = members
        self.photo = photo


#ENDPOINTS
@app.post("/api/login")
def login(data: LoginRequest):
    USERNAME = os.getenv("WWRS_USER")
    PASSWORD = os.getenv("WWRS_PASS")
    if data.username == USERNAME and data.password == PASSWORD:
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

    
@app.post("/api/groups")
def post_groups(data: GroupRequest):
    try:
        app_cache.pop("paddler_sheet", None)
        create_group(group_name=data.group_name, members=data.member_names)
        app_cache.pop("groups_data",None)
        app_cache.pop("paddler_data",None)
        return {"status": "success", "message": f"Successfully created group '{data.group_name}'!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        


@app.post("/api/trip-log")
async def post_trip_log(trip_data: TripLogSchema = Depends()):
    try:
        current_date = datetime.now().strftime("%d-%m-%y-%H%M%S")
        
        if trip_data.photo:
            print("STEP 1: Authentication")

            file_name = f"{current_date}.png"
            GOOGLE_DRIVE_FOLDER = "18A8fiJMwyx_5rZmK1qu-JmYK9BOyAXb5"
            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            TOKEN_FILE = "token.json"
            
            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )
            # Refresh the access token automatically if necessary
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
            
            drive = build(
                "drive",
                "v3",
                credentials=creds
            )
            
            print("STEP 2: Preparing Google Drive upload")

            file_metadata = {
                "name": file_name,
                "parents": [GOOGLE_DRIVE_FOLDER]
            }
            
            print("STEP 3: Seeking to beginning of uploaded file")
            trip_data.photo.file.seek(0, 2)
            file_size = trip_data.photo.file.tell()
            trip_data.photo.file.seek(0)

            print("PHOTO SIZE:", file_size)
            print("PHOTO TYPE:", trip_data.photo.content_type)
            
            media = MediaIoBaseUpload(
                trip_data.photo.file,
                mimetype=trip_data.photo.content_type,
                resumable=True
            )

            
            
            
            print("STEP 4: Uploading")
            uploaded_file = drive.files().create(
                body=file_metadata,
                media_body=media,
                fields="id,name"
            ).execute()
            
            print(uploaded_file)

            
            
            
            
            # --- LOCAL SAVE ---
            IMAGE_FOLDER = "./static/trip_photos"
            os.makedirs(IMAGE_FOLDER, exist_ok=True) # Ensure directory exists
            local_path = os.path.join(IMAGE_FOLDER, file_name)
            
            trip_data.photo.file.seek(0)
            with open(local_path, "wb") as buffer:
                shutil.copyfileobj(trip_data.photo.file, buffer)
                
        # --- SHEET APPEND & CACHE CLEARING ---
        trip_log_sheet = find_worksheet("Trip Log 4")
        trip_log_sheet.append_row([
            current_date,
            trip_data.location,
            trip_data.message,
            trip_data.members
        ])
        
        app_cache.pop("trips", None)
        app_cache.pop("files", None)
        
        return {"status": "success", "message": "Trip entry written successfully."}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
      
    

@app.get("/api/paddlers")
def get_paddlers():
    # Load your custom paddlers spreadsheet data
    if "paddler_sheet" in app_cache:
        df = app_cache["paddler_sheet"]
    else:
        df = read_form(write_to_sheet=True)
        handle_groups(df)
        app_cache["paddler_sheet"] = df
    
    # Force column headers to lowercase and convert to standard JSON list format
    df_output = df.copy()
    df_output.columns = df_output.columns.str.lower()
    return df_output.to_dict(orient="records")

@app.get("/api/groups")
def get_groups():
    try:
        groups_data = app_cache["groups_data"]
        paddler_data = app_cache["paddler_data"]
        # Convert it to a clean standard list of dictionaries
        return {"status": "success", "groups": groups_data}
        
    except KeyError:
        # Pull down your saved group names and tracking codes
        directory = find_worksheet("Groups Directory 3")
        paddler_data_sheet = find_worksheet("Paddler Data 2")
        groups_data = directory.get_all_records()
        paddler_data = paddler_data_sheet.get_all_records()
        
        # Add members
        groups_data = sort_members(groups_data,paddler_data)
        
        app_cache["groups_data"] = groups_data
        app_cache["paddler_data"] = paddler_data
        
        # Convert it to a clean standard list of dictionaries
        return {"status": "success", "groups": groups_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/trip-log")
def get_trip_log():
    try:
        if "trips" not in app_cache or "files" not in app_cache:
            trip_log_sheet = find_worksheet("Trip Log 4")
            trips = trip_log_sheet.get_all_records()
            
            drive_files = list_drive_photos()
            
            IMAGE_FOLDER = "./static/trip_photos"
            local_files = [{"name": filename} for filename in os.listdir(IMAGE_FOLDER)]
            local_names = {f["name"] for f in local_files}
            missing_files = [f for f in drive_files if f["name"] not in local_names]
            
            download_drive_photos(missing_files)
            
            
            combined_files_dict = {f["name"]: f for f in (drive_files + local_files)}
            files = list(combined_files_dict.values())
            
            app_cache["trips"] = trips
            app_cache["files"] = files
            
            return {"status": "success", "trips": trips[::-1], "files": files[::-1]}
            
        
        else:
            trips = app_cache["trips"]
            files = app_cache["files"]
            
            return {"status": "success", "trips": trips[::-1], "files": files[::-1]}
    
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_index():
    return FileResponse("index.html")








