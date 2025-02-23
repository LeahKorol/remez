# Standard Library imports

# Core Flask imports
from flask import session, request, jsonify, current_app

# Third-party imports

# App imports
from app.api import bp
from app.decorators import auth_required
from app.services import firestore_service as fs

@bp.route('/add-query', methods=['POST'])
@auth_required
def add_query():
    user_id = session['user']['uid']
    data = request.get_json()  # Parse incoming JSON data
    query_name = data.get('query_name')
    query_text = data.get('query_text')

    # Add query to Firestore
    if not query_name or not query_text:
        return jsonify({'error': 'Missing query name or text'}), 400
    try:
        # Call the create_query function
        query_dta = fs.create_query(user_id, query_name, query_text)
        return jsonify(query_dta), 201  # Return the result with a 201 status code (Created)
    except RuntimeError as e:
        current_app.logger.error(f"Creating query failed: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500
