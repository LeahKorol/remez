# Example DB service functions
_db_store = {}

def get_query(query_id: int):
    # Dummy query retrieval
    return {"query_id": query_id, "data": "example data"}

def save_results(query_id: int, results):
    # Dummy save
    _db_store[query_id] = results
