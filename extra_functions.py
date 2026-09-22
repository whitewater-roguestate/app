# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 12:47:23 2026

@author: joere
"""
import numpy as np
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from datetime import datetime
import os
import json
import base64
import requests
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv, find_dotenv

# Authenticate using ENVIRONMENT VARIABLE
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

load_dotenv()
base64_string = os.getenv("GOOGLE_CREDS_BASE64")
decoded_bytes = base64.b64decode(base64_string)
creds_dict = json.loads(decoded_bytes.decode("utf-8"))
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
gc = gspread.authorize(creds)





def find_worksheet(sheet_name):
    
    spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pI007JsK5eiZD91V77IhkXfAZ7gDiZ7ShfVOI9Jg7ZM/edit?gid=1462193928#gid=1462193928")
    worksheet = spreadsheet.worksheet(sheet_name)
    
    return worksheet


def read_form(write_to_sheet=False):
    
    response_sheet = find_worksheet("Form Responses")

    # 4. Get all records as a list of dictionaries
    data = response_sheet.get_all_records()
    df = pd.DataFrame(data)

    #NAME
    name = df["Name"].values

    #AGE
    age = df["Age"].values

    #EXPERIENCE
    experience_desc = df["Paddling Experience"].values
    experience = []
    for i in experience_desc:
        if i == "Have never been in a boat before":
            experience.append("0")
        elif i == "Have kayaked but never done whitewater":
            experience.append("0.5")
        elif i == "Paddled grade 1/2":
            experience.append("1")
        elif i == "Comfortable on 1/2 progressing onto grade 3":
            experience.append("2")
        elif i == "Comfortable on grade 3":
            experience.append("3")
        elif i == "Grade 4 nutcase":
            experience.append("4")
        elif i == "admin":
            experience.append("admin")
        elif i == "undefined":
            experience.append("undefined")
        else:
            experience.append("other")

            
    #PRIORITY
    current_date = datetime.now()
    join_dates = df["Timestamp"].values
    priority = []
    for i in join_dates:
        strip = datetime.strptime(i, "%m/%d/%Y %H:%M:%S")
        delta = current_date - strip
        priority.append(str(delta.days)+"d")
    
    #COMENTS
    member_desc = df["Are you an LUCC member?"].values
    member = []
    for i in member_desc:
        if i == "I'm a fresher":
            member.append("fresher")
        elif i == "I'm a returner":
            member.append("returner")
        elif i == "I'm a friend of the club":
            member.append("associate")
        elif i == "I somehow found this form by accident":
            member.append("stranger")
        else:
            member.append(i)
                    
    interests = df["Tell us about what kind of trips you're interested in"].values

    friends = df["Do you have any friends you'd prefer to paddle with?"].values
    important = df["Anything else we should know? (injuries, past trauma, medical conditions, etc)"].values
    aditional = df["Any comments or questions?"].values

    comments = []
    for i in range(len(name)):
        string = f"Member? {member[i]}\nInterested in: {interests[i]}\nFriends with: {friends[i]}\nImportant info: {important[i]}\nAditional comments: {aditional[i]}"
        if experience[i] == "other":
            string = string+f"\nExperience: {experience_desc[i]}"
        comments.append(string)
    
        
    data_formatted = {"name":name,"age":age,"experience":experience,"priority":priority,"comments":comments}
    df2 = pd.DataFrame(data_formatted)
    
    
    if write_to_sheet == True:
        paddler_sheet = find_worksheet("Paddler List 1")
        set_with_dataframe(paddler_sheet,df2)
    
    return df2

def handle_groups(df_form):
    worksheet = find_worksheet("Paddler Data 2")
    form_names = list(df_form["name"].values)
    try:
        # Get existing records as a DataFrame
        existing_df = get_as_dataframe(worksheet).dropna(how='all')
    except Exception:
        # Fallback if the sheet is completely empty or brand new
        existing_df = pd.DataFrame(columns=["name", "groups", "trips"])
    if not existing_df.empty:
        existing_names = list(existing_df["name"].values)
    else:
        existing_names = []   
    
    new_rows = []
    for name in form_names:
        # Protect existing data: Skip if they are already in the database
        if name in existing_names:
            continue
        
        # Initialize default values for the new user
        new_rows.append({
            "name": name,
            "groups": "",  # Clean, empty string ready for comma appending later
            "trips": 0
        })
        
    if new_rows:
        new_users_df = pd.DataFrame(new_rows)
        # Append new users to the bottom of our existing records dataframe
        updated_df = pd.concat([existing_df, new_users_df], ignore_index=True)
        
        # Clean up any weird pandas layout artifacts before pushing to Google Sheets
        updated_df = updated_df.loc[:, ~updated_df.columns.str.contains('^Unnamed')]
        
        # Rewrite the worksheet cleanly with the merged records
        set_with_dataframe(worksheet, updated_df)
    
    
    

    
def create_group(group_name=None,members=[]):
    
    #update group directory
    directory = find_worksheet("Groups Directory 3")
    groups_df = get_as_dataframe(directory)
    
    if not groups_df.empty and "code" in groups_df.columns:
        # Force the column to strings first, drop empties, and filter out text artifacts like "nan"
        valid_codes = groups_df["code"].astype(str).dropna().values
        valid_codes = [int(float(c)) for c in valid_codes if c.strip() != "" and c != "nan"]
        
        new_code = int(max(valid_codes) + 1) if len(valid_codes) > 0 else 1
    else:
        new_code = 1
        
        
    if group_name == "":
        group_name = "Group "+str(new_code)
    directory.append_row([group_name,new_code])
    
    
    
    #update paddler profiles
    profiles = read_form()
    paddler_data_sheet = find_worksheet("Paddler Data 2")
    old_data = get_as_dataframe(paddler_data_sheet).dropna(how='all')
    old_data["groups"] = old_data["groups"].astype(str)
    
    new_data = old_data.copy()
    for i in members:
        if i in new_data["name"].values:
            
            
            raw_val = new_data.loc[new_data["name"] == i, "groups"].values[0]
            
            if pd.isna(raw_val):
                current_groups = ""
            else:
                # Convert float outputs like 1.0 safely back into "1"
                current_groups = str(raw_val).replace(".0", "").strip()

            # Handle empty cells cleanly
            if current_groups == "" or current_groups == "0" or current_groups == "nan":
                updated_groups = str(new_code)
            else:
                # Split them into a clean Python list, add the new code, merge back with commas
                group_list = [g.strip() for g in current_groups.split(",") if g.strip()]
                if str(new_code) not in group_list:
                    group_list.append(str(new_code))
                updated_groups = ",".join(group_list)

            new_data.loc[new_data["name"] == i, "groups"] = updated_groups
            
            
    set_with_dataframe(paddler_data_sheet,new_data)
    

def sort_members(groups_data,paddler_data):
    
    for i in groups_data:
        members = []
        for j in paddler_data:
            code = str(i["code"])
            if code in str(j["groups"]):
                members.append(j["name"])
        members = ",".join(members)
        i.update({"members":members})
    return groups_data
                

def list_drive_photos():
    
    GOOGLE_DRIVE_FOLDER = "18A8fiJMwyx_5rZmK1qu-JmYK9BOyAXb5"
    list_url = "https://www.googleapis.com/drive/v3/files"
    params = {
        'q': f"'{GOOGLE_DRIVE_FOLDER}' in parents and trashed=false",
        'fields': 'files(id, name)',
        'supportsAllDrives': True,
        'includeItemsFromAllDrives': True
    }
    
    session = gc.http_client.session
    
    response = session.get(list_url, params=params, timeout=30)
    response.raise_for_status()
    
    files = response.json().get('files', [])
    return files



def download_drive_photos(missing_files):
    
    IMAGE_FOLDER = "./static/trip_photos"  
    session = gc.http_client.session
    
    for file in missing_files:
        file_id = file['id']
        file_name = file['name']
        
        # Define where to save this file locally
        local_path = os.path.join(IMAGE_FOLDER, file_name)
        
        # Performance check: skip downloading if we already have the photo on disk
        if os.path.exists(local_path):
            print(f"Skipping: {file_name} (Already exists locally)")
            continue
            
        print(f"Downloading: {file_name}...")
        
        # 5. Drive endpoint layout for downloading raw binary data
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        download_params = {'alt': 'media','supportsAllDrives': True}
        
        # Stream the download so we don't overload server RAM
        img_response = session.get(download_url, params=download_params, stream=True)
        
        if img_response.status_code == 200:
            # Write binary data to disk in small, efficient pieces
            with open(local_path, "wb") as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Saved: {file_name}")
        else:
            print(f"Failed to download {file_name}. Status: {img_response.status_code}")
    
    
        
    
        
    
    





    


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
