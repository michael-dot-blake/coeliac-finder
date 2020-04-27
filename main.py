from flask import Flask, render_template, request, make_response, redirect
from flask_api import status
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token
import datetime
import pyrebase
import os
from urllib.error import HTTPError
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "coeliacfinder-ad558fd97c1d.json"

config = {
    "apiKey": "AIzaSyA5ptybqH1F-VvomPE-srz5x9tOc8vQ-Bk",
    "authDomain": "coeliacfinder.firebaseapp.com",
    "databaseURL": "https://coeliacfinder.firebaseio.com",
    "storageBucket": "coeliacfinder.appspot.com"
}

firebase = pyrebase.initialize_app(config)

app = Flask(__name__)

datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


@app.route('/')
def root():
    # Verify Firebase auth.
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None

    if id_token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved performance,
            # some applications may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            print("\nClaims = ")
            print(claims)

            # Get a reference to the auth service
            auth = firebase.auth()

            user = auth.get_account_info(id_token)
        
            print("\nUserID = " + user['users'][0]['localId'])
            print("\nEmail = " + user['users'][0]['email'])

            # db = firebase.database()
            # users = db.child("users").get(id_token)
            # print("\n Users = ")
            # print(users.val())
        except ValueError as exc:
            # This will be raised if the token is expired or any other
            # verification checks fail.
            error_message = str(exc)
            print(error_message)

    return render_template(
        'index.html',
        user_data=claims, error_message=error_message, times=times)


@app.route('/login', methods=['POST'])
def login():
    # Get a reference to the auth service
    auth = firebase.auth()

    # Log the user in
    try:
        user = auth.sign_in_with_email_and_password(
            request.form['email'], request.form['password'])

        resp = make_response("Success")  # , redirect('/')
        resp.status_code = 200
        resp.set_cookie('token', user['idToken'])
        return resp
    except Exception as e:
        error_json = e.args[1]
        error = json.loads(error_json)['error']
        print(error['message'])

        switcher = {
            "INVALID_PASSWORD": "Invalid email or password",
            "EMAIL_NOT_FOUND": "Invalid email or password",
            "TOO_MANY_ATTEMPTS_TRY_LATER : Too many unsuccessful login attempts. Please try again later.": "Too many unsuccessful login attempts. Please try again later."
        }
        resp = make_response(switcher.get(
            error['message'], "Error on switch (" + error['message'] + "). Please report to Admin"))
        resp.status_code = 401
        return resp


@app.route('/signup', methods=['POST'])
def signup():
    # Get a reference to the auth service
    auth = firebase.auth()

    # Create user account
    try:
        auth.create_user_with_email_and_password(
            request.form['email'], request.form['password'])

        # Get a reference to the database service
        db = firebase.database()

        # data to save
        data = {
            "firstName": request.form['firstName'],
            "lastName": request.form['lastName'],
            "username": request.form['username']
        }

        # Log the user in
        user = auth.sign_in_with_email_and_password(
            request.form['email'], request.form['password'])

        # Pass the user's idToken to the push method
        results = db.child("users").push(data, user['idToken'])

        resp = make_response("Success")
        resp.status_code = 200
        return resp
    except Exception as e:
        error_json = e.args[1]
        error = json.loads(error_json)['error']
        print(error['message'])

        switcher = {
            "EMAIL_EXISTS": "Email already in use"
        }
        resp = make_response(switcher.get(
            error['message'], "Error on switch (" + error['message'] + "). Please report to Admin"))
        resp.status_code = 400
        return resp

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.delete_cookie('token')  # delete cookie
    return resp


@app.route('/forgotpassword', methods=['POST'])
def forgotPassword():
    # Get a reference to the auth service
    auth = firebase.auth()
    try:
        # Send password rest email
        auth.send_password_reset_email(request.form['email'])

        resp = make_response("Success")
        resp.status_code = 200
        return resp
    except Exception as e:
        error_json = e.args[1]
        error = json.loads(error_json)['error']
        print(error['message'])

        switcher = {
            "EMAIL_NOT_FOUND": "Email not found"
        }
        resp = make_response(switcher.get(
            error['message'], "Error on switch (" + error['message'] + "). Please report to Admin"))
        resp.status_code = 400
        return resp


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
