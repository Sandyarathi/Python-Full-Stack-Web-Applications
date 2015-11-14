from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from Moviesdatabase_setup import Base, Collection, Movie

# imports for google oauth
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Movie Store"

#Connect to Database and create database session
engine = create_engine('sqlite:///collections.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

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
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user is not connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token.
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

#Show catalog home page
@app.route('/', methods = ['GET'])
@app.route('/catalog/', methods = ['GET'])
def showCatalog():
  collections = session.query(Collection).order_by(asc(Collection.name))
  movies = session.query(Movie).order_by(asc(Movie.year))
  #return render_template('catalog.html', collections=collections, movies = movies)
  return jsonify(Collections =[c.serialize for c in collections], Movies = [m.serialize for m in movies])


#To Show a collection movies
@app.route('/catalog/collection/<int:collection_id>/',methods = ['GET'])
@app.route('/catalog/collection/<int:collection_id>/movies/', methods = ['GET'])
def showCollectionAllMovies(collection_id):
    collection = session.query(Collection).filter_by(id = collection_id).one()
    movies = session.query(Movie).filter_by(collection_id = collection_id).all()
    #return render_template('viewCollectionMovies.html', collection=collection, movies= movies)
    return jsonify(Movies=[i.serialize for i in movies])

#View a movie description
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/', methods = ['GET'])
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/description/', methods = ['GET'])
def showMovieDescription(collection_id,movie_id):
  movie = session.query(Movie).filter_by(id = movie_id).one()
  #return render_template('viewMovieDescription.html', movie=movie)
  return jsonify(Movie = movie.serialize)


#Create a new collection
@app.route('/catalog/collection/new/', methods = ['POST'])
def newCollection():
  if request.method == 'POST':
    if not ('name' in request.json):
      response = jsonify({'result': 'ERROR'})
      response.status_code = 400
      return response
    else:
      newCol = Collection(name= request.json['name'])
      session.add(newCol)
      session.commit()
      flash("New Collection Added!")
      return jsonify(NewCollection = newCol.serialize)

#Edit a collection
@app.route('/catalog/collection/<int:collection_id>/edit/', methods=['GET','POST'])
def editCollection(collection_id):
  editedCollection = session.query(Collection).filter_by(id = collection_id).one()
  if request.method == 'POST':
    if ('name' in request.json):
      editedCollection.name = request.json['name']
      session.add(editedCollection)
      session.commit()
      return jsonify(EditedCollection = editedCollection.serialize)
    else:
      return jsonify(EditedCollection = editedCollection.serialize)

#Delete a collection
@app.route('/catalog/collection/<int:collection_id>/delete/', methods = ['GET','POST'])
def deleteCollection(collection_id):
  colToDelete = session.query(Collection).filter_by(id=collection_id).one()
  if request.method == 'POST':
    session.delete(colToDelete)
    session.commit()
    return jsonify(DeletedCollection = colToDelete.serialize)

#Create a new movie
@app.route('/catalog/collection/<int:collection_id>/movie/new/', methods = ['GET','POST'])
def newMovie(collection_id):
  if(request.method == 'POST'):
    newMovie = Movie(name = request.json['name'],
      director = request.json['director'],
      genre = request.json['genre'],
      year = request.json['year'],
      description = request.json['description'],
      cover_image = request.json['cover_image'],
      trailer_URL = request.json['trailer_URL'],
      collection_id=collection_id)
    session.add(newMovie)
    session.commit()
    return jsonify(NewMovie = newMovie.serialize)

#Edit an movie
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/edit/', methods =['GET','POST'])
def editMovie(collection_id,movie_id):
  editedMovie = session.query(Movie).filter_by(id=movie_id).one()
  if(request.method == 'POST'):
    if 'name' in request.json:
      editedMovie.name = request.json['name']
    if 'director' in request.json:
      editedMovie.director = request.json['director']
    if 'genre' in request.json:
      editedMovie.genre = request.json['genre']
    if 'year' in request.json:
      editedMovie.year = request.json['year']
    if 'description' in request.json:
      editedMovie.description= request.json['description']
    if 'cover_image' in request.json:
      editedMovie.cover_image = request.json['cover_image']
    if 'trailer_URL' in request.json:
      editedMovie.trailer_URL= request.form['trailer_URL']
    session.add(editedMovie)
    session.commit()
    return jsonify(EditedMovie = editedMovie.serialize)

#Delete an movie
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/delete/', methods =['GET','POST'])
def deleteMovie(collection_id, movie_id):
  movieToDelete = session.query(Movie).filter_by(id=movie_id).one()
  if request.method == 'POST':
      session.delete(movieToDelete)
      session.commit()
      return jsonify(DeletedMovie = movieToDelete.serialize)



if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
