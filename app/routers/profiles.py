from fastapi import APIRouter, Request
from services import sheets
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

router = APIRouter()


@router.get("")
async def get_paddlers(request: Request):
    logger.info("Get paddlers request recieved")
    await request.app.state.prefetch_ready.wait()
    
    
    data = sheets.get_local_cache()
    paddler_data = data["Paddler List 1"]
    trip_data = data["Trip Log 4"]
    logger.debug(f"paddler data: {paddler_data}")
    df = pd.DataFrame(paddler_data)
    
    # Calculate trips column
    df["trips"] = np.zeros(len(paddler_data))
    paddler_names = df["name"].values
    trip_members = [d["members"] for d in trip_data]
    logger.debug(f"paddlers on trips: {trip_members}")
    logger.debug(f"all paddlers: {paddler_names}")
    for name in paddler_names:
        count = 0
        for t in trip_members:
            #logger.debug(f"{t}")
            if name in t:
                count += 1
        df.loc[df["name"] == name,"trips"] = count
        
                
    
    
    # Extract the numeric number of days from priority, e.g. "17d" -> 17
    df["_priority_days"] = (df["priority"].str.replace("d", "", regex=False).astype(int))
    data_sorted = df.sort_values(by=["trips", "_priority_days"], ascending=[True, False])
    data_sorted = data_sorted.drop(columns=["_priority_days"])
    
    logger.debug(f"final df: {data_sorted}")
    
    
    return data_sorted.to_dict(orient="records")
    
    
