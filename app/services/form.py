from fastapi import APIRouter, HTTPException
import logging
from services import sheets
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__name__)

router = APIRouter()




def format_responses(responses):
    # Load data dynamically handling either a list of records or a dictionary
    df = pd.DataFrame(responses)
    
    # 1. EXPERIENCE MAPPING (Using a clean dictionary lookup)
    exp_map = {
        "Have never been in a boat before": "0",
        "Have kayaked but never done whitewater": "0.5",
        "Paddled grade 1/2": "1",
        "Comfortable on 1/2 progressing onto grade 3": "2",
        "Comfortable on grade 3": "3",
        "Grade 4 nutcase": "4",
        "undefined": "undefined"
    }
    
    # Use .map() for bulk conversion, handle 'admin' case, and fill leftovers with 'other'
    experience = df["Paddling Experience"].map(exp_map)
    experience.loc[df["Paddling Experience"].str.lower() == "admin"] = "admin"
    experience = experience.fillna("other")

    # 2. PRIORITY / TIMESTAMP CALCULATIONS
    # errors='coerce' prevents crashes; format='mixed' handles variations in Google Forms
    timestamps = pd.to_datetime(df["Timestamp"], errors='coerce', format='mixed')
    days_delta = (datetime.now() - timestamps).dt.days
    priority = days_delta.fillna(0).astype(int).astype(str) + "d"

    # 3. CLUB MEMBERSHIP MAPPING
    member_map = {
        "I'm a fresher": "fresher",
        "I'm a returner": "returner",
        "I'm a friend of the club": "associate",
        "I somehow found this form by accident": "stranger"
    }
    member = df["Are you an LUCC member?"].map(member_map).fillna(df["Are you an LUCC member?"])

    # 4. VECTORISED COMMENT GENERATION
    # Vectorised string concatenation avoids manual looping completely
    comments = (
        "Member? " + member.astype(str) + "\n" +
        "Interested in: " + df["Tell us about what kind of trips you're interested in"].astype(str) + "\n" +
        "Friends with: " + df["Do you have any friends you'd prefer to paddle with?"].astype(str) + "\n" +
        "Important info: " + df["Anything else we should know? (injuries, past trauma, medical conditions, etc)"].astype(str) + "\n" +
        "Aditional comments: " + df["Any comments or questions?"].astype(str)
    )
    
    # Append raw experience string if mapped result is 'other'
    other_mask = experience == "other"
    comments.loc[other_mask] = comments + "\nExperience: " + df.loc[other_mask, "Paddling Experience"].astype(str)

    # 5. CONSTRUCT FINAL DATAFRAME AND RETURN
    # No risk of index mismatch because columns remain bound to the dataframe structure
    data_formatted = pd.DataFrame({
        "name": df["Name"],
        "age": df["Age"],
        "experience": experience,
        "priority": priority,
        "comments": comments
    })

    return data_formatted.to_dict(orient="records")
