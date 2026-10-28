#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 15:25:29 2026

@author: joere
"""
from fastapi import APIRouter
from dotenv import load_dotenv
import base64
import json
import os
import gspread
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"]


def get_credentials():
    
    TOKEN_FILE = "token.json"
    
    
    CREDS_FILE = "credentials.json" 
    
    creds = None
    
    # 1. Try to load the token (it won't find it, which is fine)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
    # 2. Since it doesn't exist, this block will run and create it:
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...", flush=True)
            creds.refresh(Request())
        else:
            print("Token missing. Launching Google Browser Login Flow...", flush=True)
            
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(f"Put your credentials.json file here: {os.path.abspath(CREDS_FILE)}")
                
            # This opens your web browser automatically
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=0, 
                access_type='offline', 
                prompt='consent'
            )
            
        # Automatically write brand new token.json file
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
            print("Success! Brand new token.json has been generated.", flush=True)
            
    return creds

get_credentials()