import time
from typing import Dict

# simulation of a database or persistent storage
STATUS: Dict[int, Dict] = {}

def run_pipeline(query_id: int):
    STATUS[query_id] = {"status": "running", "progress": 0, "result": None}
    
    # here we get the parameters from DB (Django Models or ORM other)
    # params = get_query_params(query_id)
    
    for i in range(1, 11):
        time.sleep(1)  # simulate work
        STATUS[query_id]["progress"] = i * 10

    # here we connect to report.main(...) or marked_data.main(...)
    result = {"example": "pipeline finished"}  

    STATUS[query_id] = {
        "status": "done",
        "progress": 100,
        "result": result
    }

def get_status(query_id: int):
    return STATUS.get(query_id, {"status": "not_found"})
