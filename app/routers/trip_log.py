from fastapi import APIRouter, HTTPException
from fastapi import Depends, Form, UploadFile, File
from services import sheets, drive
import logging
import os
from datetime import datetime
from googleapiclient.http import MediaIoBaseUpload
import shutil


logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

router = APIRouter()


class TripLogSchema:
    def __init__(
        self,
        location: str = Form(...),
        message: str = Form(...),
        group: str | None = Form(""),
        photo: UploadFile | None = File(None)
    ):
        self.location = location
        self.message = message
        self.group = group
        self.photo = photo
        
        
        


@router.get("")
def get_trip_log():
    try:
        trip_record = sheets.get_local_cache()["Trip Log 4"]
        drive_files = drive.list_drive_photos()
        
        IMAGE_FOLDER = "./static/trip_photos"
        local_files = [{"name": filename} for filename in os.listdir(IMAGE_FOLDER)]
        local_names = {f["name"] for f in local_files}
        missing_files = [f for f in drive_files if f["name"] not in local_names]
        
        drive.download_drive_photos(missing_files)
    
        combined_files_dict = {f["name"]: f for f in (drive_files + local_files)}
        files = list(combined_files_dict.values())
        
        return {"status": "success", "trips": trip_record[::-1], "files": files[::-1]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        


@router.delete("")
def delete_log_post(trip_ref: str):
    try:
        log = sheets.get_local_cache()["Trip Log 4"]
        
        row = next(
            (
                i for i, item in enumerate(log)
                if str(item.get("date", "")).strip() == str(trip_ref)
            ),
            None
        )
        
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Trip with data {trip_ref} not found"
            )
        
        # Delete from local cache
        del log[row]
        master_data = sheets.get_local_cache()
        master_data["Trip Log 4"] = log
        sheets.save_local_cache(master_data, sheets.get_local_timestamp())
        
        # Delete from google sheet
        sheets.delete_row_from_sheet("Trip Log 4", row + 2)

        return {
            "status": "success",
            "message": f"Deleted trip {trip_ref} and removed its log post"
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
        
        


        
    

        
@router.post("")
def post_trip_log(trip_data: TripLogSchema = Depends()):
    try:
        current_date = datetime.now().strftime("%d-%m-%y-%H%M%S")
        
        if trip_data.photo:
            file_name = f"{current_date}.png"
            logger.info("STEP 1: Authentication")
            service = drive.get_drive_client()
            
            logger.info("STEP 2: Preparing Google Drive upload")
            GOOGLE_DRIVE_FOLDER = "18A8fiJMwyx_5rZmK1qu-JmYK9BOyAXb5"
            file_metadata = {
                "name": file_name,
                "parents": [GOOGLE_DRIVE_FOLDER]
            }
        
            logger.info("STEP 3: Seeking to beginning of uploaded file")
            trip_data.photo.file.seek(0, 2)
            file_size = trip_data.photo.file.tell()
            trip_data.photo.file.seek(0)

            logger.info(f"PHOTO SIZE: {file_size}")
            logger.info(f"PHOTO TYPE: {trip_data.photo.content_type}")
            
            media = MediaIoBaseUpload(
                trip_data.photo.file,
                mimetype=trip_data.photo.content_type,
                resumable=True
            )
            
            logger.info("STEP 4: Uploading")
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id,name"
            ).execute()
            
            logger.info(uploaded_file)
            
            # --- LOCAL SAVE ---
            IMAGE_FOLDER = "./static/trip_photos"
            os.makedirs(IMAGE_FOLDER, exist_ok=True) # Ensure directory exists
            local_path = os.path.join(IMAGE_FOLDER, file_name)
            trip_data.photo.file.seek(0)
            with open(local_path, "wb") as buffer:
                shutil.copyfileobj(trip_data.photo.file, buffer)
        
        # Get trip paddlers
        group_code = str(trip_data.group).strip().removesuffix(".0")
        logger.info(f"Group code: {group_code}")
        directory = sheets.get_local_cache()["Groups Directory 3"]
        log = sheets.get_local_cache()["Trip Log 4"]
        logger.debug(f"{directory}")
        members = next((d["members"] for d in directory if str(d["code"]) == group_code), "")
        for d in directory:
            logger.debug(f"group data code: {d['code']}")
        logger.info(f"Trip paddlers: {members}")        
        
        
        # --- LOCAL RECORDS APPEND --- #
        log.append({"date": current_date, "location": trip_data.location, "message": trip_data.message, "members": members})
        master_data = sheets.get_local_cache()
        master_data["Trip Log 4"] = log
        sheets.save_local_cache(master_data, sheets.get_local_timestamp())
        
        
        # --- SHEET APPEND ---
        row_data = [current_date, trip_data.location, trip_data.message, members]
        logger.info("Appending group row process started...")
        sheets.append_row_to_sheet("Trip Log 4", row_data)
        logger.info(f"Process finished")
        
        return {"status": "success", "message": "Trip entry written successfully."}
                
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
        




