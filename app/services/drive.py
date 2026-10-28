from fastapi import APIRouter, HTTPException
import logging
from services import sheets
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload
import os

logger = logging.getLogger(__name__)

router = APIRouter()





def get_drive_client():
    """Returns an authorized gspread client sharing the core credentials."""
    creds = sheets.get_credentials()
    service = build("drive","v3",credentials=creds)
    return service



def list_drive_photos():
    GOOGLE_DRIVE_FOLDER = "18A8fiJMwyx_5rZmK1qu-JmYK9BOyAXb5"
    
    service = get_drive_client()
    files = []
    page_token = None

    while True:
        # Call the API to fetch a page of files
        response = service.files().list(
            q=f"'{GOOGLE_DRIVE_FOLDER}' in parents and trashed=false",
            pageSize=100,                                
            fields="nextPageToken, files(id, name)",    
            pageToken=page_token                        
        ).execute()
        
        # Extract files from the current page response
        page_files = response.get('files', [])
        files.extend(page_files)
        
        # Check if there is another page of results
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
        
    return files



def download_drive_photos(missing_files):
    
    IMAGE_FOLDER = "./static/trip_photos"
    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    
    service = get_drive_client()
    
    for file in missing_files:
        file_id = file['id']
        file_name = file['name']
        
        # Define where to save this file locally
        local_path = os.path.join(IMAGE_FOLDER, file_name)
        
        # Performance check: skip downloading if we already have the photo on disk
        if os.path.exists(local_path):
            logger.info(f"Skipping: {file_name} (Already exists locally)")
            continue
        
        logger.info(f"Downloading: {file_name}...")
    
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        while True:
            status, done = downloader.next_chunk()
            logger.info(f"Progress: {int(status.progress() * 100)}%")
            
            if done:
                break
        
        fh.seek(0)
        with open(local_path, "wb") as f:
            f.write(fh.read())
            logger.info(f"Saved: {file_name}")
        
        
    







