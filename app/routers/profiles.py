from fastapi import APIRouter, Request, HTTPException
from services import sheets, form
import logging
import pandas as pd
from collections import Counter
import traceback


logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

router = APIRouter()


@router.get("")
async def get_paddlers(request: Request):
    try:
        logger.info("Get paddlers request recieved")
        await request.app.state.prefetch_ready.wait()
        
        
        data = sheets.get_local_cache()
        paddler_data = data["Paddler List 1"]
        trip_data = data["Trip Log 4"]
        logger.debug(f"paddler data: {paddler_data}")
        df = pd.DataFrame(paddler_data)
        
        # Calculate trips column.
        # Paddlers are identified by email: a trip counts for a paddler when their email
        # is one of the entries in that trip's member_emails list. Entries are compared
        # whole (not as substrings) after normalising case/whitespace, and blank emails
        # never match anyone.
        paddler_emails = df["email"].map(form.normalize_email)
        trip_counts = Counter()
        for t in trip_data:
            emails_on_trip = {e for e in form.split_email_list(t.get("member_emails", "")) if e}
            logger.debug(f"emails on trip: {emails_on_trip}")
            trip_counts.update(emails_on_trip)
        logger.debug(f"all paddlers: {paddler_emails.values}")
        df["trips"] = paddler_emails.map(lambda e: trip_counts.get(e, 0))
            
                    
        
        
        # Extract the numeric number of days from priority, e.g. "17d" -> 17
        df["_priority_days"] = (df["priority"].str.replace("d", "", regex=False).astype(int))
        data_sorted = df.sort_values(by=["trips", "_priority_days"], ascending=[True, False])
        data_sorted = data_sorted.drop(columns=["_priority_days"])
        
        logger.debug(f"final df: {data_sorted}")
        
        
        return data_sorted.to_dict(orient="records")
    
    
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))