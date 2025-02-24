# Standard Library imports

# Core Flask imports
from flask import current_app

# Third-party imports
from firebase_admin import firestore, exceptions

# App imports
from app.db.firebase import Firebase


# Firestore collections
USERS_COLLECTION = "users"
QUERIES_COLLECTION = "queries"


def get_db():
    return Firebase.get_firestore()


def get_user_queries(uid):
    db = get_db()
    user_ref = db.collection(USERS_COLLECTION).document(uid)
    queries_ref = user_ref.collection(QUERIES_COLLECTION).stream()
    queries = [{"id": doc.id, **doc.to_dict()} for doc in queries_ref]
    return [query.to_dict() for query in queries]


def create_query(uid, query_name, query_text):
    db = get_db()
    query_data = {
        "name": query_name,
        "text": query_text,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    try:
        user_queris_ref = (
            db.collection(USERS_COLLECTION).document(uid).collection(QUERIES_COLLECTION)
        )
        _, new_query_ref = user_queris_ref.add(query_data)
        # Return the query data along with the document ID
        return new_query_ref.id

    except exceptions.FirebaseError as e:
        current_app.logger.error(f"Query creation failed: {e}")
        raise e
