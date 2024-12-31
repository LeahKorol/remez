from flask import Flask, redirect, render_template, request, make_response, session, abort, jsonify, url_for
import secrets
from functools import wraps
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()



app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configure session cookie settings
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are sent over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Adjust session expiration as needed
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Can be 'Strict', 'Lax', or 'None'


# Firebase Admin SDK setup
cred = credentials.Certificate("firebase-auth.json")
firebase_admin.initialize_app(cred)
db = firestore.client()



########################################
""" Authentication and Authorization """

# Decorator for routes that require authentication
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if 'user' not in session:
            return redirect(url_for('login'))
        
        else:
            return f(*args, **kwargs)
        
    return decorated_function


@app.route('/auth', methods=['POST'])
def authorize():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return "Unauthorized", 401

    token = token[7:]  # Strip off 'Bearer ' to get the actual token

    try:
        decoded_token = auth.verify_id_token(token) # Validate token here
        session['user'] = decoded_token # Add user to session
        return redirect(url_for('dashboard'))
    
    except:
        return "Unauthorized", 401


#####################
""" Public Routes """

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/signup')
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('signup.html')


@app.route('/reset-password')
def reset_password():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('forgot_password.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from session
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)  # Optionally clear the session cookie
    return response


##############################################
""" Private Routes (Require authorization) """

# @app.route('/dashboard')
# @auth_required
# def dashboard():

#     return render_template('dashboard.html')

@app.route('/dashboard')
@auth_required
def dashboard():
    user_id = session['user']['uid']
    # Retrieve all queries for the logged-in user
    queries_ref = db.collection('queries').where('user_id', '==', user_id)
    queries = queries_ref.stream()
    query_list = [query.to_dict() for query in queries]
    print(query_list)

    return render_template('dashboard.html', queries=query_list)

##############################################
""" Ensure firestore works """
@app.route('/add-query', methods=['POST'])
@auth_required
def add_query():
    user_id = session['user']['uid']
    data = request.get_json()  # Parse incoming JSON data
    query_name = data.get('query_name')
    query_text = data.get('query_text')

    # Add query to Firestore
    if query_name and query_text:
        query_ref = db.collection('queries').add({
            'user_id': user_id,
            'query_name': query_name,
            'query_text': query_text
        })
        return redirect(url_for('dashboard'))
    else:
        return jsonify({'error': 'Query name and text are required'}), 400



if __name__ == '__main__':
    # TODO: install a self ssl certificate instead of this dummy certificate
    app.run(debug=True, ssl_context='adhoc')
