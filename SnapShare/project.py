from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "SnapShare"

#Connect to Database and create database session
engine = create_engine('sqlite:///PhotoCollections.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
@app.route('/SnapShare/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/SnapShare/gconnect', methods=['POST'])
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
    newUser = User(name= login_session['username'], id=login_session['user_id'], email= login_session['email'],imageURL =login_session['picture'])
    session.add(newUser)
    session.commit()
    return output

@app.route('/SnapShare/gdisconnect')
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

# To show home page albums & photos
@app.route('/SnapShare', methods = ['GET'])
@app.route('/SnapShare/catalog/', methods = ['GET'])
def showCatalog():
  print "in show catalog"
  albums = session.query(Album).order_by(asc(Album.name))
  photos = session.query(Photo).order_by(asc(Photo.year))
  #return render_template('catalog.html', albums=albums, photos = photos)
  return jsonify(Albums =[a.serialize for a in albums], Photos = [p.serialize for p in photos])

#To Show a album
@app.route('/SnapShare/catalog/album/<int:album_id>/',methods = ['GET'])
@app.route('/SnapShare/catalog/album/<int:album_id>/photos/', methods = ['GET'])
def showAlbumAllPhotos(album_id):
    album = session.query(Album).filter_by(id = album_id).one()
    photos = session.query(Photo).filter_by(album_id = album_id).all()
    #return render_template('viewAlbumPhotos.html', album=album, photos= photos)
    return jsonify(Photos=[i.serialize for i in photos])

#View a photo description
@app.route('/SnapShare/catalog/album/<int:album_id>/photo/<int:photo_id>/', methods = ['GET'])
@app.route('/SnapShare/catalog/album/<int:album_id>/photo/<int:photo_id>/description/', methods = ['GET'])
def showPhotoDescription(album_id,photo_id):
  photo = session.query(Photo).filter_by(id = photo_id).one()
  #return render_template('viewPhotoDescription.html', photo=photo)
  return jsonify(Photo = photo.serialize)


#Create a new album
@app.route('/SnapShare/catalog/album/new/', methods = ['POST'])
def newAlbum():
  if 'username' not in login_session:
        return redirect('/SnapShare/login')
  if request.method == 'POST':
    if not ('name' in request.json):
      response = jsonify({'result': 'ERROR'})
      response.status_code = 400
      return response
    else:
      newCol = Album(name= request.json['name'], user_id=login_session['user_id'])
      session.add(newCol)
      session.commit()
      flash("New Album Added!")
      return jsonify(NewAlbum = newCol.serialize)

#Edit a album
@app.route('/SnapShare/catalog/album/<int:album_id>/edit/', methods=['GET','POST'])
def editAlbum(album_id):
  editedAlbum = session.query(Album).filter_by(id = album_id).one()
  if 'username' not in login_session:
        return redirect('/SnapShare/login')
  if editedAlbum.user_id != login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
                "to edit this collection. Please create your own collection in"
                " order to edit.');}</script><body onload='myFunction()'>")
  if request.method == 'POST':
    if ('name' in request.json):
      editedAlbum.name = request.json['name']
      session.add(editedAlbum)
      session.commit()
      return jsonify(EditedAlbum = editedAlbum.serialize)
    else:
      return jsonify(EditedAlbum = editedAlbum.serialize)

#Delete a album
@app.route('/SnapShare/catalog/album/<int:album_id>/delete/', methods = ['GET','POST'])
def deleteAlbum(album_id):
  colToDelete = session.query(Album).filter_by(id=album_id).one()
  if 'username' not in login_session:
    return redirect('/login')
  if colToDelete.user_id != login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
            "to delete this collection. Plaease create your own collection"
            " in order to delete.');}</script><body onload='myFunction()'"
            ">")
  if request.method == 'POST':
    session.delete(colToDelete)
    session.commit()
    return jsonify(DeletedAlbum = colToDelete.serialize)

#Create a new photo
@app.route('/SnapShare/catalog/album/<int:album_id>/photo/new/', methods = ['GET','POST'])
def newPhoto(album_id):
  if 'username' not in login_session:
        return redirect('/SnapShare/login')
  if(request.method == 'POST'):
    newPhoto = Photo(name = request.json['name'],
      location = request.json['location'],
      year = request.json['year'],
      description = request.json['description'],
      image = request.json['image'],
      album_id=album_id,
      user_id=login_session['user_id'])
    session.add(newPhoto)
    session.commit()
    return jsonify(NewPhoto = newPhoto.serialize)

#Edit an photo
@app.route('/SnapShare/catalog/album/<int:album_id>/photo/<int:photo_id>/edit/', methods =['GET','POST'])
def editPhoto(album_id,photo_id):
  editedPhoto = session.query(Photo).filter_by(id=photo_id).one()
  if 'username' not in login_session:
        return redirect('/SnapShare/login')
  if editedPhoto.user_id != login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
                "to edit this photo. Please add your own photo in"
                " order to edit.');}</script><body onload='myFunction()'>")
  if(request.method == 'POST'):
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
    return jsonify(EditedPhoto = editedPhoto.serialize)

#Delete an photo
@app.route('/SnapShare/catalog/album/<int:album_id>/photo/<int:photo_id>/delete/', methods =['GET','POST'])
def deletePhoto(album_id, photo_id):
  photoToDelete = session.query(Photo).filter_by(id=photo_id).one()
  if 'username' not in login_session:
      return redirect('/login')
  if photoToDelete.user_id != login_session['user_id']:
      return ("<script>function myFunction() {alert('You are not authorized "
                "to delete this photo. Please delete from your own "
                " collection.');}</script><body onload='myFunction()'"
                ">")
  if request.method == 'POST':
      session.delete(photoToDelete)
      session.commit()
      return jsonify(DeletedPhoto = photoToDelete.serialize)




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
