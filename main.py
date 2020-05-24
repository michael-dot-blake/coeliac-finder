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
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, fields
from flask.json import jsonify
import uuid
from sqlalchemy.orm.strategy_options import joinedload

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "coeliacfinder-ad558fd97c1d.json"

config = {
    "apiKey": "AIzaSyA5ptybqH1F-VvomPE-srz5x9tOc8vQ-Bk",
    "authDomain": "coeliacfinder.firebaseapp.com",
    "databaseURL": "https://coeliacfinder.firebaseio.com",
    "storageBucket": "coeliacfinder.appspot.com"
}

firebase = pyrebase.initialize_app(config)
firebase_request_adapter = requests.Request()

app = Flask(__name__)
app.config['FLASK_APP'] = "main.py"

# +=============================================================+
# |                                                             |
# |                          SQLAchemy                          |
# |                                                             |
# +=============================================================+

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://dbuser:6S#2WV6S%QD&-uJF@34.87.224.162/coeliacfinder?unix_socket=/cloudsql/coeliacfinder:australia-southeast1:coeliacfinder'
if __name__ == '__main__':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://dbuser:6S#2WV6S%QD&-uJF@34.87.224.162/coeliacfinder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Users(db.Model):
    id = db.Column(db.String(32), unique=True,
                   nullable=False, primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False)
    username = db.Column(db.String(24), unique=True, nullable=False)
    firstName = db.Column(db.String(24))
    lastName = db.Column(db.String(24))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    reviews = db.relationship('Reviews', backref='users', lazy=True)

class Places(db.Model):
    id = db.Column(db.String(20), unique=True,
                   nullable=False, primary_key=True)
    streetAddress = db.Column(db.String(255), nullable=False)
    suburb = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    postCode = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255))
    reviews = db.relationship('Reviews', backref='places', lazy=True)

class Reviews(db.Model):
    id = db.Column(db.String(42), unique=True, nullable=False,
                   primary_key=True)  # CHECK TYPE
    placeId = db.Column(db.String(20), db.ForeignKey(
        'places.id'), nullable=False)
    place = db.relationship("Places", backref="places")
    userId = db.Column(db.String(32), db.ForeignKey(
        'users.id'), nullable=False)
    user = db.relationship("Users", backref="users")
    text = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

db.create_all()

class SmartNested(ma.Nested): 
    def serialize(self, attr, obj, accessor=None):
        if attr not in obj.__dict__:
            return {"id": int(getattr(obj, attr + "_id"))}
        return super(SmartNested, self).serialize(attr, obj, accessor)

class UsersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        include_relationships = True
        load_instance = True

    # reviews = ma.Nested(ReviewsSchema)

class ReviewsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Reviews
        include_fk = True
        load_instance = True
    
    user = ma.Nested(UsersSchema)

class PlacesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Places
    
    # reviews = ma.Nested(ReviewsSchema)


# +=============================================================+
# |                                                             |
# |                            Routes                           |
# |                                                             |
# +=============================================================+


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
            "INVALID_EMAIL": "Invalid email or password",
            "EMAIL_NOT_FOUND": "Invalid email or password",
            "TOO_MANY_ATTEMPTS_TRY_LATER : Too many unsuccessful login attempts. Please try again later.": "Too many unsuccessful login attempts. Please try again later."
        }
        resp = make_response(switcher.get(
            error['message'], "Error on switch (" + error['message'] + "). Please report to Admin"))
        resp.status_code = 401
        return resp


@app.route('/signup', methods=['POST'])
def signup():
    # Check for blank username
    if (request.form['username'] == ""):
        resp = make_response("Username cannot be blank")
        resp.status_code = 401
        return resp

    # Create user account
    try:
        # Check if username taken
        if Users.query.filter_by(username=request.form['username']).first() != None:
            resp = make_response("Username already in use")
            resp.status_code = 401
            return resp

        # Get a reference to the auth service
        auth = firebase.auth()
        auth.create_user_with_email_and_password(
            request.form['email'], request.form['password'])

        user = auth.sign_in_with_email_and_password(
            request.form['email'], request.form['password'])

        # Inset user data into db
        data = Users(id=user['localId'], email=request.form['email'], username=request.form['username'],
                     firstName=request.form['firstName'], lastName=request.form['lastName'])

        db.session.add(data)
        db.session.commit()

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
            "EMAIL_NOT_FOUND": "Email not found",
            "MISSING_EMAIL": "Please enter an email address"
        }
        resp = make_response(switcher.get(
            error['message'], "Error on switch (" + error['message'] + "). Please report to Admin"))
        resp.status_code = 400
        return resp


@app.route('/changedetails', methods=['GET', 'POST'])
def user_details():
    id_token = request.cookies.get("token")
    auth = firebase.auth()
    user = auth.get_account_info(id_token)
    userID = user['users'][0]['localId']
    targetUser = Users.query.filter_by(id=userID).first()

    if request.method == 'POST':
        # Check if username taken
        if Users.query.filter_by(username=request.form['username']).first() != None:
            resp = make_response("Username already in use")
            resp.status_code = 401
            return resp

        if request.form['username'] != "":
            targetUser.username = request.form['username']
        if request.form['firstName'] != "":
            targetUser.firstName = request.form['firstName']
        if request.form['lastName'] != "":
            targetUser.firstName = request.form['lastName']

        db.session.commit()

        resp = make_response("Success")
        resp.status_code = 200
        return resp

    resp = make_response(jsonify(
        username=targetUser.username,
        firstName=targetUser.firstName,
        lastName=targetUser.lastName
    ))
    resp.status_code = 200
    resp.content_type = "application/json"
    return resp


@app.route('/changepassword')
def change_password():
    id_token = request.cookies.get("token")
    auth = firebase.auth()
    user = auth.get_account_info(id_token)
    user_email = user['users'][0]['email']
    auth.send_password_reset_email(user_email)

    resp = make_response("Success")
    resp.status_code = 200
    return resp


@app.route('/deleteaccount')
def delete_accout():
    try:
        id_token = request.cookies.get("token")
        auth = firebase.auth()
        user = auth.get_account_info(id_token)
        userID = user['users'][0]['localId']
        targetUser = Users.query.filter_by(id=userID).first()

        # Delete from Firebase
        auth.delete_user_account(id_token)

        # Delete from CloudSQL
        db.session.delete(targetUser)
        db.session.commit()

        resp = make_response("Success")
        resp.delete_cookie('token')  # delete cookie
        resp.status_code = 200
        return resp
    except Exception as e:
        error_json = e.args[1]
        error = json.loads(error_json)['error']
        print(error['message'])

        switcher = {
            "CREDENTIAL_TOO_OLD_LOGIN_AGAIN": "Credentials too old"
        }
        resp = make_response(switcher.get(
            error['message'], "Error on switch (" + error['message'] + "). Please report to Admin"))
        resp.status_code = 400
        return resp


def add_place():
    # Check if place exists in db
    if Places.query.filter_by(id=request.form['id']).first() != None:
        return

    # Inset place data into db
    data = Places(id=request.form['id'], streetAddress=request.form['streetAddress'], suburb=request.form['suburb'],
                  state=request.form['state'], postCode=request.form['postCode'], country=request.form['country'],
                  lat=request.form['lat'], lon=request.form['lon'], name=request.form['name'], category=request.form['category'])

    db.session.add(data)
    db.session.commit()
    return


@app.route('/reviews', methods=['POST'])
def add_review():
    print(request.form['id'])
    add_place()

    # Generate uuid for review ID
    id = str(uuid.uuid4())

    # Get user ID
    id_token = request.cookies.get("token")
    auth = firebase.auth()
    user = auth.get_account_info(id_token)
    userId = user['users'][0]['localId']

    # Inset review data into db
    data = Reviews(
        id=id, placeId=request.form['id'], userId=userId, text=request.form['text'])

    db.session.add(data)
    db.session.commit()

    resp = make_response("Success")
    resp.status_code = 200
    return resp


@app.route('/places')
def get_all_places():
    places = Places.query.all()
    places_schema = PlacesSchema(many=True)
    output = places_schema.dump(places)

    resp = jsonify({'places': output})
    resp.status_code = 200
    resp.content_type = "application/json"
    return resp

@app.route('/reviews/places/<placeId>')
def get_reviews_place(placeId):
    reviews = Reviews.query.filter_by(placeId=placeId).all()
    reviews_schema = ReviewsSchema(many=True)
    output = reviews_schema.dump(reviews)

    resp = jsonify({'reviews': output})
    resp.status_code = 200
    resp.content_type = "application/json"
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
