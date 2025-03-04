# Standard Library imports

# Core Flask imports
from flask import render_template, session, redirect, url_for, make_response

# Third-party imports

# App imports
from app.main import bp
from app.utils.decorators import auth_required

#####################
""" Public Routes """


@bp.route("/")
def home():
    return render_template("home.html")


@bp.route("/login")
def login():
    if "idToken" in session:
        return redirect(url_for("main.logout"))
    else:
        return render_template("login.html")


@bp.route("/signup")
def signup():
    if "idToken" in session:
        return redirect(url_for("main.logout"))
    else:
        return render_template("signup.html")


@bp.route("/reset-password")
def reset_password():
    if "idToken" in session:
        return redirect(url_for("main.logout"))
    else:
        return render_template("forgot_password.html")


@bp.route("/terms")
def terms():
    return render_template("terms.html")


@bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@bp.route("/logout")
def logout():
    session.pop("user", None)  # Remove the user from session
    response = make_response(redirect(url_for("main.login")))
    response.set_cookie("session", "", expires=0)  # Optionally clear the session cookie
    return response


##############################################
""" Private Routes (Require authorization) """


@bp.route("/dashboard")
@auth_required
@bp.doc(security="FirebaseSessionAuth")
def dashboard():
    return render_template("dashboard.html")
