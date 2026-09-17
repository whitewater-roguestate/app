# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 12:47:23 2026

@author: joere
"""
import numpy as np
import pandas as pd
import gspread
from datetime import datetime
import os
import json
from dotenv import load_dotenv, find_dotenv
import base64



def convert_df():
    load_dotenv(find_dotenv())
    # 1. Authenticate using ENVIRONMENT VARIABLE
    base64_string = os.getenv("GOOGLE_CREDS_BASE64")
    decoded_bytes = base64.b64decode(base64_string)
    creds_dict = json.loads(decoded_bytes.decode("utf-8"))
    gc = gspread.service_account_from_dict(creds_dict)
    # 2. Open the spreadsheet by its name or URL
    spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pI007JsK5eiZD91V77IhkXfAZ7gDiZ7ShfVOI9Jg7ZM/edit?gid=1462193928#gid=1462193928")
    # 3. Select the specific worksheet (tab)
    worksheet = spreadsheet.worksheet("Form Responses 1")

    # 4. Get all records as a list of dictionaries
    data = worksheet.get_all_records()

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

    #TRIPS
    trips = np.zeros(len(name))

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

        
    data_formatted = {"name":name,"age":age,"experience":experience,"priority":priority,"trips":trips,"comments":comments}
    df2 = pd.DataFrame(data_formatted,columns=["name", "age", "experience", "priority", "trips", "comments"],)
    
    return df2

convert_df()