# Standard Library imports

# Core Flask imports

# Third-party imports

# App imports
from ..firebase_init import FirebaseApp

db = FirebaseApp.get_firestore()

def get_user_queries(user_id):
    queries_ref = db.collection('queries').where('user_id', '==', user_id)
    queries = queries_ref.stream()
    return [query.to_dict() for query in queries]

def create_query(user_id, query_name, query_text):
    query_data = {
        'user_id': user_id,
        'query_name': query_name,
        'query_text': query_text
    }
    try:
        _, query_ref = db.collection('queries').add(query_data)
        # Return the query data along with the document ID
        return {**query_data, 'id': query_ref.id}
    except Exception as e:
        print(f"Error adding query to Firestore: {e}")
        raise RuntimeError("Failed to create the query in Firestore.")

