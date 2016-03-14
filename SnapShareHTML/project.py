from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)


import datetime
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from Albumsdatabase_setup import Base, Album, Photo

# imports for google oauth
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "SnapShare"

#Connect to Database and create database session
engine = create_engine('sqlite:///PhotoCollections.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
@app.route('/login')
def showLogin():
  '''User login method.'''
  state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
  login_session['state'] = state
  # return "The current session state is %s" % login_session['state']
  return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
  '''Login method to handle Google OAuth.'''
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

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    
    output = ' Successfully logged in!'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions


def createUser(login_session):
  '''Method to create a new user record when a new user logs in to the application.'''
  newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
  session.add(newUser)
  session.commit()
  user = session.query(User).filter_by(email=login_session['email']).one()
  return user.id


def getUserInfo(user_id):
  '''Retrieve user information from user model'''
  user = session.query(User).filter_by(id=user_id).one()
  return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
  '''Google disconnect method to log out.'''
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

def login_required(func):
  """ Decorator function that ensures user login before create, 
      update or delete operations.

      Args: 
        func: Function to decorate.
  """
  @wraps(func)
  def function_wrapper(*args, **kwargs):
    print "in login check"
    if 'username' not in login_session:
      flash('Please login to add or edit.')
      return jsonify(msg='Logging in is required to do this!')
    return func(*args, **kwargs)
  return function_wrapper



# JSON APIs to view albums
@app.route('/album/<int:album_id>/JSON')
def albumPhotosJSON(album_id):
  albums = session.query(Album).filter_by(id = album_id).one()
  photos= session.query(Photo).filter_by(album_id=album_id).all()
  return jsonify(Photos=[p.serialize for p in photos])

@app.route('/album/<int:album_id>/<int:photo_id>/JSON')
def photoJSON(album_id, photo_id):
    photo = session.query(Photo).filter_by(id = photo_id).one()
    return jsonify(photo = photo.serialize)

@app.route('/album/JSON')
def albumsJSON():
    albums = session.query(Album).all()
    return jsonify(albums = [i.serialize for i in albums])
    



# To show home page albums & photos
@app.route('/catalog/', methods = ['GET'])
def showCatalog():
  '''Method to display contents of the home page of SnapShare application!'''
  print "in show catalog"
  albums = session.query(Album).order_by(asc(Album.name))
  photos = session.query(Photo).order_by(asc(Photo.year))
  #return render_template('catalog.html', albums=albums, photos = photos)
  #return jsonify(Albums =[a.serialize for a in albums], Photos = [p.serialize for p in photos])
  if 'username' not in login_session:
    return render_template('publicCatalog.html', albums=albums, photos = photos )
  else:
    return render_template('catalog.html', albums=albums, photos = photos)


#To Show an album
@app.route('/catalog/album/<int:album_id>/',methods = ['GET'])
@app.route('/catalog/album/<int:album_id>/photos/', methods = ['GET'])
def showAlbumAllPhotos(album_id):
  '''Method to display photos corresponding to a particular album'''
  try:
    album = session.query(Album).filter_by(id = album_id).first()
    if album:
      photos = session.query(Photo).filter_by(album_id = album_id).all()
      creator = getUserInfo(album.user_id)
      if photos != []:
        #return render_template('viewAlbumPhotos.html', album=album, photos= photos)
        return jsonify(Photos=[p.serialize for p in photos])
      else:
        return jsonify(msg='No photos in this album!')
    else:
      return jsonify(msg='Album with this id doesnot exist!')
  except Exception, e:
      print str(e)
      return jsonify(msg = 'Error occured while processsing request!')

#View a photo description
@app.route('/catalog/album/<int:album_id>/photo/<int:photo_id>/', methods = ['GET'])
@app.route('/catalog/album/<int:album_id>/photo/<int:photo_id>/description/', methods = ['GET'])
def showPhotoDescription(album_id,photo_id):
  '''Method to view the description of a particular photo.'''
  try:
    album= session.query(Album).filter_by(id= album_id).first()
    if album:
      photo = session.query(Photo).filter_by(id = photo_id).first()
      if photo:
        #return render_template('viewPhotoDescription.html', photo=photo)
        return jsonify(Photo = photo.serialize)
      else:
        return jsonify(msg='No photo with this id!')
    else:
        return jsonify(msg='No album with this id!')
  except Exception, e:
    print str(e)
    return jsonify(msg = 'Error occured while processsing request!')




#Create a new album
@app.route('/catalog/album/new/', methods = ['POST'])
@login_required
def newAlbum():
  '''Method to create a new album in the catalog'''
  if request.method == 'POST':
    try:
      newCol = Album(name= request.json['name'],
        user_id=login_session['user_id'])
      session.add(newCol)
      session.commit()
      flash("New Album Added!")
      #return jsonify(added=True, NewAlbum = newCol.serialize)
      return redirect(url_for('showCatalog'))
    except Exception, e:
      print str(e)
      return jsonify(added = False, msg='Unable to add!')
  else:
    #return jsonify(added = False, masg='Exited from request method!')
    return render_template('newAlbum.html')
#Edit a album
@app.route('/catalog/album/<int:album_id>/edit/', methods=['GET','POST'])
@login_required
def editAlbum(album_id):
  '''Method to edit the attributes of an album.'''
  if request.method == 'POST':
    try:
      editedAlbum = session.query(Album).filter_by(id = album_id).one()
      if editedAlbum:
        if editedAlbum.user_id != login_session['user_id']:
          return ("<script>function myFunction() {alert('You are not authorized "
                "to edit this collection. Please create your own collection in"
                " order to edit.');}</script><body onload='myFunction()'>")
          if ('name' in request.json):
            editedAlbum.name = request.json['name']
            session.add(editedAlbum)
            session.commit()
            #return jsonify(updated=True, EditedAlbum = editedAlbum.serialize, msg='Record has been updated!')
            return redirect(url_for('showCatalog'))
      else:
        return jsonify(updated=False, msg='No such album exists!')
    except Exception, e:
      print str(e)
      return jsonify(EditedAlbum = editedAlbum.serialize, updated=False, msg='An error occured while trying to update!')
  else:
    #return jsonify(updated=False, msg='An error occured while updating!')
    return render_template('editAlbum.html', album = editedAlbum)

#Delete a album
@app.route('/catalog/album/<int:album_id>/delete/', methods = ['GET','POST'])
@login_required
def deleteAlbum(album_id):
  '''Method to delete a particular album.'''
  if request.method == 'POST':
    try:
      colToDelete = session.query(Album).filter_by(id=album_id).one()
      if colToDelete:
        if colToDelete.user_id != login_session['user_id']:
          return ("<script>function myFunction() {alert('You are not authorized "
                "to delete this collection. Plaease create your own collection"
                " in order to delete.');}</script><body onload='myFunction()'"
                ">")
        session.delete(colToDelete)
        session.commit()
        #return jsonify(deleted=True, msg='Record has been deleted!')
        return redirect(url_for('showcatalog', album_id=album_id))
      else:
        return jsonify(deleted=False, msg='No such Album exists!')
    except Exception, e:
      print str(e)
      return jsonify(deleted=False, msg='An error occured while trying to delete!')
  else:
    #return jsonify(deleted=False, msg='An error occured while deleting!')
    return render_template('deleteAlbum.html', album = colToDelete)

#Create a new photo
@app.route('/catalog/album/<int:album_id>/photo/new/', methods = ['GET','POST'])
@login_required
def newPhoto(album_id):
  '''Method to add a new photo to an album.'''
  if(request.method == 'POST'):
    try:
      newPhoto = Photo(name = request.json['name'],
        location = request.json['location'],
        year = request.json['year'],
        description = request.json['description'],
        image = request.json['image'],
        album_id=album_id,
        user_id=login_session['user_id'])
      session.add(newPhoto)
      session.commit()
      return jsonify(added=True, NewPhoto = newPhoto.serialize)
    except Exception, e:
      print str(e)
      return jsonify(added = False)
  else:
    return jsonify(added = False)

#Edit an photo
@app.route('/catalog/album/<int:album_id>/photo/<int:photo_id>/edit/', methods =['GET','POST'])
@login_required
def editPhoto(album_id,photo_id):
  '''Method to edit the attributes of a Photo in an album.'''
  if(request.method == 'POST'):
    try:
      editedPhoto = session.query(Photo).filter_by(id=photo_id).one()
      if editedPhoto:
        if editedPhoto.user_id != login_session['user_id']:
          return ("<script>function myFunction() {alert('You are not authorized "
                    "to edit this photo. Please add your own photo in"
                    " order to edit.');}</script><body onload='myFunction()'>")
        if 'name' in request.json:
          editedPhoto.name = request.json['name']
        if 'location' in request.json:
          editedPhoto.director = request.json['location']
        if 'year' in request.json:
          editedPhoto.year = request.json['year']
        if 'description' in request.json:
          editedPhoto.description= request.json['description']
        if 'image' in request.json:
          editedPhoto.cover_image = request.json['image']
        session.add(editedPhoto)
        session.commit()
        return jsonify(updated = True, EditedPhoto = editedPhoto.serialize, msg='Record updated!')
      else:
        return jsonify(updated=False, msg='No such photo exists!')
    except Exception, e:
      print str(e)
      return jsonify(EditedPhoto = editedAlbum.serialize, updated=False, msg='An error occured while trying to update!')
  else:
    return jsonify(updated=False, msg='An error occured while updating!')



#Delete an photo
@app.route('/catalog/album/<int:album_id>/photo/<int:photo_id>/delete/', methods =['GET','POST'])
@login_required
def deletePhoto(album_id, photo_id):
  '''Method to delete a photo from the album.'''
  if request.method == 'POST':
    try:
      photoToDelete = session.query(Photo).filter_by(id=photo_id).one()
      if photoToDelete:
        if photoToDelete.user_id != login_session['user_id']:
            return ("<script>function myFunction() {alert('You are not authorized "
                      "to delete this photo. Please delete from your own "
                      " collection.');}</script><body onload='myFunction()'"
                      ">")
        
        session.delete(photoToDelete)
        session.commit()
        return jsonify(deleted=True, DeletedPhoto = photoToDelete.serialize)
      else:
        return jsonify(deleted=False, msg='No such Photo exists!')
    except Exception, e:
      print str(e)
      return jsonify(deleted=False, msg='An error occured while trying to delete!')
  else:
    return jsonify(deleted=False, msg='An error occured while deleting!')




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
