from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import gspread
from convert_responses import convert_df

app = FastAPI()

# Allow connections from any device (essential for local phone testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

    


class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "lucc":
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/paddlers")
def get_paddlers():
    # Load your custom paddlers spreadsheet data
    try:
        df = convert_df()
    except FileNotFoundError:
        # Fallback if the file isn't present
        df = pd.DataFrame({
            "name": ["empty", "empty"],
            "age": [0, 0],
            "experience": [0, 0],
            "group": [0, 0],
            "comments": ["Clouds float high...", "When the sun shines..."]
        })
    # Force column headers to lowercase and convert to standard JSON list format
    df.columns = df.columns.str.lower()
    return df.to_dict(orient="records")

@app.get("/")
def read_index():
    return FileResponse("index.html")
