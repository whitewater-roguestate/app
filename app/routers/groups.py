from fastapi import APIRouter, HTTPException
import logging
from services import sheets
import pandas as pd
import time
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

router = APIRouter()


class GroupRequest(BaseModel):
    group_name: str
    member_names: list[str]
    
    
    

@router.get("")
def get_groups():
    try:
        group_directory = sheets.get_local_cache()["Groups Directory 3"]
        logger.debug(f"{group_directory}")
        
        return {"status": "success", "groups": group_directory}
    
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.delete("")
def delete_group(group_id: int):
    try:
        directory = sheets.get_local_cache()["Groups Directory 3"]

        row = next(
            (
                i for i, item in enumerate(directory)
                if str(item.get("code", "")).strip() == str(group_id)
            ),
            None
        )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Group with code {group_id} not found"
            )

        # Delete from local cache
        del directory[row]
        master_data = sheets.get_local_cache()
        master_data["Groups Directory 3"] = directory
        sheets.save_local_cache(master_data, sheets.get_local_timestamp())

        # Delete from google sheet
        sheets.delete_row_from_sheet("Groups Directory 3", row + 2)

        return {
            "status": "success",
            "message": f"Deleted group {group_id} and removed its membership codes"
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        






@router.post("")
def post_groups(data: GroupRequest):
    try:
        master_data = sheets.get_local_cache()
        directory = master_data["Groups Directory 3"]
        df = pd.DataFrame(directory)
        if not df.empty:
            # Force the column to strings first, drop empties, and filter out text artifacts like "nan"
            valid_codes = df["code"].astype(str).dropna().values
            valid_codes = [int(float(c)) for c in valid_codes if c.strip() != "" and c != "nan"]
            new_code = int(max(valid_codes) + 1) if len(valid_codes) > 0 else 1
        else:
            new_code = 1
            
        
        data.member_names = ", ".join(data.member_names)

            
        # Append the new group to local file
        directory.append({'group_name': data.group_name, 'code': new_code, 'members': data.member_names})
        master_data["Groups Directory 3"] = directory
        sheets.save_local_cache(master_data, sheets.get_local_timestamp())
        
        # Append the new group to spreadsheet
        row_data = [data.group_name, new_code, data.member_names]
        start_time = time.perf_counter()
        logger.info("Appending group row process started...")
        sheets.append_row_to_sheet("Groups Directory 3", row_data)
        duration = time.perf_counter() - start_time
        logger.info(f"Process finished in {duration:.4f} seconds")
        
        return {"status": "success", "message": f"Successfully created group '{data.group_name}'"}

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))











