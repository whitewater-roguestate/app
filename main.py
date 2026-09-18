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

df = convert_df()    


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
    df = convert_df()
    # Force column headers to lowercase and convert to standard JSON list format
    df.columns = df.columns.str.lower()
    return df.to_dict(orient="records")

@app.get("/")
def read_index():
    return FileResponse("index.html")
