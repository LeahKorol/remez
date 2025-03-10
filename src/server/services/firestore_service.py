# Standard Library imports
from typing import Dict, Optional, List

# Core Flask imports

# Third-party imports
from firebase_admin import firestore

# App imports
from app.db.firebase import Firebase


# Firestore collections
USERS_COLLECTION = "users"
QUERIES_COLLECTION = "queries"


def get_db():
    return Firebase.get_firestore()


def create_user_query(uid: str, query_name: str, query_text: str) -> Dict[str, str]:
    """
    Create a new query document for a user in Firestore.

    Args:
        uid: The ID of the user.
        query_name: The name of the query.
        query_text: The query content.

    Returns:
        A dictionary containing the ID & the creation time of the newly created query document.

    Raises:
        firebase_admin.exceptions.FirebaseError: If Firestore operation fails.
    """
    db = get_db()
    query_data = {
        "name": query_name,
        "text": query_text,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    user_queries_ref = (
        db.collection(USERS_COLLECTION).document(uid).collection(QUERIES_COLLECTION)
    )
    _, query_ref = user_queries_ref.add(query_data)
    return {"id": query_ref.id, **query_ref.get().to_dict()}


def get_user_query(uid: str, query_id: str) -> Optional[Dict[str, str]]:
    """
    Fetch a specific query document for a user from Firestore.

    Args:
        uid: The user ID.
        query_id: The Firestore document ID of the query.

    Returns:
        A dictionary with query data if found, else None.

    Raises:
        firebase_admin.exceptions.FirebaseError: If Firestore operation fails.
    """
    db = get_db()
    user_ref = db.collection(USERS_COLLECTION).document(uid)
    query_ref = user_ref.collection(QUERIES_COLLECTION).document(query_id)
    query = query_ref.get()

    if not query.exists:
        return None

    return {"id": query.id, **query.to_dict()}


def get_user_queries(uid: str) -> Optional[List[Dict[str, str]]]:
    """
    Retrieve all queries associated with a user from Firestore.

    Args:
        uid: The ID of the user.

    Returns:
        A list of dictionaries, each representing a query document.
        Returns an empty list if no queries exist.

    Raises:
        firebase_admin.exceptions.FirebaseError: If Firestore operation fails.
    """
    db = get_db()
    user_ref = db.collection(USERS_COLLECTION).document(uid)

    queries_ref = user_ref.collection(QUERIES_COLLECTION)
    queries = [{"id": doc.id, **doc.to_dict()} for doc in queries_ref.stream()]
    return queries if queries else []


def update_user_query(
    uid: str,
    query_id: str,
    query_name: Optional[str] = None,
    query_text: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """
    Update an existing query document for a user in Firestore.

    Args:
        uid: The ID of the user.
        query_id: The Firestore document ID of the query.
        query_name: The updated name of the query (optional).
        query_text: The updated content of the query (optional).

    Returns:
        A dictionary containing the updated query ID and data if successful, else None.

    Raises:
        firebase_admin.exceptions.FirebaseError: If Firestore operation fails.
    """
    db = get_db()
    user_ref = db.collection(USERS_COLLECTION).document(uid)
    query_ref = user_ref.collection(QUERIES_COLLECTION).document(query_id)
    query = query_ref.get()

    # Query not found
    if not query.exists:
        return None

    # Prepare update data
    update_data = {}
    if query_name:
        update_data["name"] = query_name
    if query_text:
        update_data["text"] = query_text

    if update_data:
        query_ref.update(update_data)

    # Returns updated data
    return {"id": query_ref.id, **query_ref.get().to_dict()}


def delete_user_query(uid: str, query_id: str) -> Optional[Dict[str, str]]:
    """
    Delete a specific query document for a user from Firestore.

    Args:
        uid: The user ID.
        query_id: The Firestore document ID of the query.

    Returns:
        A dictionary with query id if found, else None.

    Raises:
        firebase_admin.exceptions.FirebaseError: If Firestore operation fails.
    """
    db = get_db()
    user_ref = db.collection(USERS_COLLECTION).document(uid)
    query_ref = user_ref.collection(QUERIES_COLLECTION).document(query_id)
    query = query_ref.get()

    if not query.exists:
        return None

    query_ref.delete()
    return {"id": query_ref.id}
