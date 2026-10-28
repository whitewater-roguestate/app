from fastapi import APIRouter
from dotenv import load_dotenv
import base64
import json
import os
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging
from services import form
import pandas as pd

logger = logging.getLogger(__name__)


router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"]

SPREADSHEET_KEY = "1pI007JsK5eiZD91V77IhkXfAZ7gDiZ7ShfVOI9Jg7ZM"


# Paths for caching your local state
CACHE_DATA_FILE = "services/local_sheet_data.json"
CACHE_META_FILE = "services/local_sheet_meta.txt"

def get_local_cache():
    """Reads local multi-tab data from JSON if it exists."""
    if os.path.exists(CACHE_DATA_FILE):
        with open(CACHE_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_local_cache(master_data, timestamp):
    """Saves complete workbook mapping and timestamp locally."""
    os.makedirs(os.path.dirname(CACHE_DATA_FILE), exist_ok=True)
    with open(CACHE_DATA_FILE, "w") as f:
        json.dump(master_data, f, indent=4)
    with open(CACHE_META_FILE, "w") as f:
        f.write(timestamp)
        
def get_local_timestamp():
    """Reads the last cached timestamp."""
    if os.path.exists(CACHE_META_FILE):
        with open(CACHE_META_FILE, "r") as f:
            return f.read().strip()
    return ""        
        
        
def get_credentials():
    
    TOKEN_FILE = "token.json"
    creds = Credentials.from_authorized_user_file(TOKEN_FILE,SCOPES)
    # Refresh the access token automatically if necessary
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    
    return creds
            

            

def get_gspread_client():
    """Returns an authorized gspread client sharing the core credentials."""
    creds = get_credentials()
    return gspread.Client(auth=creds)


def append_row_to_sheet(worksheet_name, row_data):
    gc = get_gspread_client()
    sh = gc.open_by_key(SPREADSHEET_KEY)
    worksheet = sh.worksheet(worksheet_name)
    worksheet.append_row(row_data, value_input_option="USER_ENTERED")

def delete_row_from_sheet(worksheet_name, index):
    gc = get_gspread_client()
    sh = gc.open_by_key(SPREADSHEET_KEY)
    worksheet = sh.worksheet(worksheet_name)
    worksheet.delete_rows(index)
    


def start_global_prefetch(SPREADSHEET_KEY):
    logger.info("starting the prefetch")
    gc = get_gspread_client()
    sh = gc.open_by_key(SPREADSHEET_KEY)
    live_timestamp = sh.get_lastUpdateTime()
    logger.info(f"Spreadsheet metadata timestamp fetched: {live_timestamp}")
    
    cached_timestamp = get_local_timestamp()
    local_data = get_local_cache()
    
    if live_timestamp == cached_timestamp and local_data:
        logger.info("Cache hit! All 5 tabs match the cloud version.")
        return {"status": "success", "source": "local_cache", "data": local_data}
    
    logger.info("Cache miss! Downloading all 5 worksheets from Google...")
    
    master_workbook_data = {}
    # Loop dynamically through every worksheet in the file
    all_worksheets = sh.worksheets()
    for worksheet in all_worksheets:
        tab_name = worksheet.title
        logger.info(f"Pulling rows from: {tab_name}")
        
        # Save as a list of key-value row dictionaries
        master_workbook_data[tab_name] = worksheet.get_all_records()
    
    # Check whether new form responses need formatting
    old_raw_responses = local_data.get("Form Responses", [])
    
    df_new_raw = pd.DataFrame(master_workbook_data["Form Responses"])
    df_old_raw = pd.DataFrame(old_raw_responses)
    if not df_new_raw.equals(df_old_raw):
        logger.info("New form responses found")
        fresh_paddlers = form.format_responses(master_workbook_data["Form Responses"])
        master_workbook_data["Paddler List 1"] = fresh_paddlers
        
        df_upload = pd.DataFrame(fresh_paddlers)
    
        target_sheet = sh.worksheet("Paddler List 1")
        target_sheet.clear()
        
        # Update google sheet with new rows
        set_with_dataframe(target_sheet, df_upload, include_index=False)
        
            
        
    # Save the combined payload under the single timestamp marker
    save_local_cache(master_workbook_data, live_timestamp)
    logger.info("Completed caching all sheets into local storage.")
    
    return {"status": "success", "source": "google_sheets", "data": master_workbook_data}
    












