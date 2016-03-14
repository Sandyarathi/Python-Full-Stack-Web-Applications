from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import url_for
from flask import flash
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from Moviesdatabase_setup  import Base
from Moviesdatabase_setup  import Collection
from Moviesdatabase_setup  import Movie
from Moviesdatabase_setup  import User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import httplib2
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Movie Catalog"

# Connect to Database and create database session
engine = create_engine('sqlite:///collections.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def login():
    # create a state token to prevent request forgery
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    # store it in session for later use
    login_session['state'] = state
    return render_template('login.html', STATE = state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Disconnect based on provider
@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCollections'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCollections'))


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# JSON APIs to view music dump
@app.route('/collection/<int:collection_id>/JSON')
def collectionMoviesJSON(collection_id):
    collection = session.query(Collection).filter_by(id = collection_id).one()
    movies = session.query(Movie).filter_by(collection_id = collection_id).all()
    return jsonify(movies = [i.serialize for i in movies])

@app.route('/collection/<int:collection_id>/<int:movie_id>/JSON')
def movieJSON(collection_id, movie_id):
    movie = session.query(Movie).filter_by(id = movie_id).one()
    return jsonify(movie = movie.serialize)

@app.route('/collection/JSON')
def collectionsJSON():
    collections = session.query(Collection).all()
    return jsonify(collections = [i.serialize for i in collections])

# Show all collections
@app.route('/')
def showCollections():
    movies = session.query(Movie).order_by(asc(Movie.name))
    collections = session.query(Collection).order_by(asc(Collection.name))
    if 'username' not in login_session:
        return render_template('publicmovies.html', movies = movies, collections = collections)
    else:
        return render_template('movies.html', movies = movies, collections = collections)

# Create a new music collection
@app.route('/collection/new', methods=['GET','POST'])
def newCollection():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCollection = Collection(name = request.form['name'],
                         user_id=login_session['user_id'])
        session.add(newCollection)
        flash('Succesfully added %s collection' % newCollection.name)
        session.commit()
        return redirect(url_for('showCollections'))
    else:
        return render_template('new-collection.html')

# Edit a collection
@app.route('/collection/<int:collection_id>/edit/', methods = ['GET', 'POST'])
def editCollection(collection_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCollection = session.query(Collection).filter_by(id = collection_id).one()
    if editedCollection.user_id != login_session['user_id']:
        return """<script>(function() {alert("not authorized");})();</script>"""
    if request.method == 'POST':
        if request.form['name']:
            editedCollection.name = request.form['name']
            flash('Collection successfully edited %s' % editedCollection.name)
            return redirect(url_for('showCollections'))
    else:
        return render_template('edit-collection.html', collection = editedCollection)

# Delete a collection
@app.route('/collection/<int:collection_id>/delete/', methods = ['GET', 'POST'])
def deleteCollection(collection_id):
    if 'username' not in login_session:
        return redirect('/login')
    collectionToDelete = session.query(Collection).filter_by(id = collection_id).one()
    if collectionToDelete.user_id != login_session['user_id']:
        return """<script>(function() {alert("not authorized");})();</script>"""
    if request.method == 'POST':
        session.delete(collectionToDelete)
        flash('%s successfully deleted' % collectionToDelete.name)
        session.commit()
        return redirect(url_for('showCollections', collection_id = collection_id))
    else:
        return render_template('delete-collection.html', collection = collectionToDelete)

# Show movies from a collection
@app.route('/collection/<int:collection_id>/')
@app.route('/collection/<int:collection_id>/movies/')
def showMovies(collection_id):
    collection = session.query(Collection).filter_by(id = collection_id).one()
    collections = session.query(Collection).order_by(asc(Collection.name))
    creator = getUserInfo(collection.user_id)
    movies = session.query(Movie).filter_by(collection_id = collection_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicmovies.html', movies = movies,
            collection = collection, collections = collections, creator = creator)
    else:
        return render_template('movies.html', movies = movies,
             collection = collection, collections = collections, creator = creator)

# Create a new movie for a collection
@app.route('/collection/<int:collection_id>/movies/new/', methods = ['GET', 'POST'])
def newMovie(collection_id):
    if 'username' not in login_session:
        return redirect('/login')
    collection = session.query(Collection).filter_by(id = collection_id).one()
    if request.method == 'POST':
        newMovie = Movie(name = request.form['name'],
            collection_id = collection_id,
            director = request.form['director'],
            genre = request.form['genre'],
            year = request.form['year'],
            description = request.form['description'],
            cover_image = request.form['cover_image'],
            trailer_URL = request.form['trailer_URL'],
            user_id = login_session['user_id'])
        session.add(newMovie)
        session.commit()
        flash('New movie %s successfully created' % (newMovie.name))
        return redirect(url_for('showMovies', collection_id = collection_id))
    else:
        return render_template('new-movie.html', collection_id = collection_id)

# Edit a movie
@app.route('/collection/<int:collection_id>/movie/<int:movie_id>/edit', methods = ['GET', 'POST'])
def editMovie(collection_id, movie_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedMovie = session.query(Movie).filter_by(id = movie_id).one()
    collection = session.query(Collection).filter_by(id = collection_id).one()
    if editedMovie.user_id != login_session['user_id']:
        return """<script>(function() {alert("not authorized");})();</script>"""
    if request.method == 'POST':
        if 'name' in request.form:
          editedMovie.name = request.form['name']
        if 'director' in request.form:
          editedMovie.director = request.form['director']
        if 'genre' in request.form:
          editedMovie.genre = request.form['genre']
        if 'year' in request.form:
          editedMovie.year = request.form['year']
        if 'description' in request.form:
          editedMovie.description= request.form['description']
        if 'cover_image' in request.form:
          editedMovie.cover_image = request.form['cover_image']
        if 'trailer_URL' in request.form:
          editedMovie.trailer_URL= request.form['trailer_URL']
        session.add(editedMovie)
        session.commit()
        flash('Movie successfully edited')
        return redirect(url_for('showMovies', collection_id = collection_id))
    else:
        return render_template('edit-movie.html', collection_id = collection_id, movie_id = movie_id, movie = editedMovie)

# Delete a movie
@app.route('/collection/<int:collection_id>/movies/<int:movie_id>/delete', methods = ['GET', 'POST'])
def deleteMovie(collection_id, movie_id):
    if 'username' not in login_session:
        return redirect('/login')
    collection = session.query(Collection).filter_by(id = collection_id).one()
    movieToDelete = session.query(Movie).filter_by(id = movie_id).one()
    if movieToDelete.user_id != login_session['user_id']:
        return """<script>(function() {alert("not authorized");})();</script>"""
    if request.method == 'POST':
        session.delete(movieToDelete)
        session.commit()
        flash('Movie successfully deleted')
        return redirect(url_for('showMovie', collection_id = collection_id))
    else:
        return render_template('delete-movie.html', movie = movieToDelete)


if __name__ == '__main__':
    app.secret_key = "secret key"
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)