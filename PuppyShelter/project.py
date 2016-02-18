from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from datetime import datetime
from datetime import timedelta
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from puppies_dbSetup import Base, Shelter, Puppy, User

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

# Initialize flask application with templates
app = Flask(__name__, template_folder='templates')

# Read the client_secrets.json file to get the client_id for google Sign-in
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "PuppiesShelter"

# Create SQLite db with name puppyshelter.db
engine = create_engine('sqlite:///puppyshelter.db')
Base.metadata.bind = engine

# Connect to Database and create database session
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Defines the folder where uploaded images may be stored
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Defines max size of image uploads < 5MB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Decorator function to check pre-conditions for certain functions
def login_required(func):
  """ Decorator function that ensures user login before create, 
      update or delete operations.
      Args: 
        func: Function to decorate.
  """
  @wraps(func)
  def function_wrapper(*args, **kwargs):
    if 'username' not in login_session:
      flash('Please login to add or edit puppies.')
      return showLogin()
    return func(*args, **kwargs)
  return function_wrapper


# This method takes the login_session object and creates a new user in the
# database
# Returns the id of newly created user
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Retreives the user information from User table in database based on user id
# Returns an object of User instance
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Based on email provided, it queries the database for the user having same
# email.
# Returns user id if found a user, other returns None
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/PuppiesShelter/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/PuppiesShelter/gconnect', methods=['POST'])
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
    login_session['provider'] = 'google'

    loginUser= getUserID(login_session['email'])
    if not loginUser:
      loginUser = createUser(login_session)
    login_session['user_id'] = loginUser
    output = 'Successfully logged in!'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/PuppiesShelter/gdisconnect')
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

@app.route('/PuppiesShelter/disconnect')
def disconnect():
  if 'provider' in login_session:
    if login_session['provider'] == 'google':
      gdisconnect()
      del login_session['gplus_id']
      del login_session['credentials']
      del login_session['username']
      del login_session['email']
      del login_session['picture']
      del login_session['user_id']
      del login_session['provider']
      flash("You have successfully been logged out.")
      return redirect(url_for('showLogin'))
  else:
    flash("You were not logged in")
    return redirect(url_for('showLogin'))

# Checks for allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Check if user has logged in or not
@app.route('/checkLoggedIn')
def checkLoggedIn():
    if 'username' not in login_session:
        return jsonify(loggedIn=False)
    else:
        if request.args.get('state') != login_session['state']:
            return jsonify(loggedIn=False)
        return jsonify(loggedIn=True)

# Handles any request which is of the
# pattern <serverdomain:port>/ or <serverdomain:port>/index
# Checks if the valid login session exists, then renders the index.html page
# from templates folder and replaces STATE, USERNAME, PICTURE according to
# context variables being set in render_template method arguments
'''@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template(
        'index.html',
        STATE=login_session['state'],
        USERNAME=login_session['username'],
        PICTURE=login_session['picture'])'''

# To show home page shelters & puppies
@app.route('/PuppiesShelter', methods = ['GET'])
@app.route('/PuppiesShelter/', methods = ['GET'])
def showCatalog():
  print "in show catalog"
  shelters = session.query(Shelter).order_by(asc(Shelter.name))
  sixMonthsAgo = datetime.now() - timedelta(weeks=12)
  puppies = session.query(Puppy).filter(Puppy.dateOfBirth > sixMonthsAgo).order_by("dateOfBirth desc")
  return render_template('index.html', shelters=shelters, puppies = puppies)
  #return jsonify(Shelters =[a.serialize for a in shelters], Puppies = [p.serialize for p in puppies])

#To Show a shelter
@app.route('/PuppiesShelter/shelter/<int:shelter_id>/all',methods = ['GET'])
@app.route('/PuppiesShelter/shelter/<int:shelter_id>/puppies/', methods = ['GET'])
def showShelterAllPuppies(shelter_id):
    shelter = session.query(Shelter).filter_by(id = shelter_id).one()
    puppies = session.query(Puppy).filter_by(shelter_id = shelter_id).all()
    return render_template('viewShelterPuppies.html', shelter=shelter, puppies= puppies)
    #return jsonify(Puppies=[i.serialize for i in puppies])

#View a puppy description
@app.route('/PuppiesShelter/puppy/<int:puppy_id>/', methods = ['GET'])
def showPuppyDescription(puppy_id):
  puppy = session.query(Puppy).filter_by(id = puppy_id).one()
  #return render_template('viewPuppyDescription.html', puppy=puppy)
  return jsonify(Puppy = puppy.serialize)


#Add a new puppy
@app.route('/PuppiesShelter/shelter/<int:shelter_id>/puppy/new/', methods = ['GET','POST'])
@login_required
def newPuppy(shelter_id):
  if(request.method == 'POST'):
    try:
      image_src = ''
      if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = time.strftime("%Y%m%d-%H%M%S") + \
                secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_src = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      shelter = session.query(Shelter).filter_by(id=shelter_id).one()
      newPuppy = Puppy(name = request.json['name'],
        gender = request.form['gender'],
        dateOfBirth = request.form['dateOfBirth'],
        breed = request.form['breed'],
        picture = image_src,
        shelter=shelter,
        weight=request.form['weight'],
        owner_id=login_session['user_id'])
      session.add(newPuppy)
      session.commit()
      return jsonify(added = True, msg='Record added!')
    except Exception, e:
      print str(e)
      return jsonify(added = False, msg='Error occured while adding!')
  else:
    return render_template('')


#Edit an puppy
@app.route('/PuppiesShelter/shelter/<int:shelter_id>/puppy/<int:puppy_id>/edit/', methods =['GET','POST'])
@login_required
def editPuppy(shelter_id,puppy_id):
  if(request.method == 'POST'):
    try:
      image_src = ''
      if ('file' in request.files):
          file = request.files['file']
          if (file and file.filename != '' and
                  allowed_file(file.filename)):
              # adding timestring to filename to prevent any
              # duplicate file uploads
              filename = time.strftime("%Y%m%d-%H%M%S") + \
                  secure_filename(file.filename)
              file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                     filename))
              image_src = os.path.join(app.config['UPLOAD_FOLDER'],
                                       filename)
      if 'name' in request.form:
        puppyName = request.form['name']
      if 'gender' in request.form:
        puppyGender = request.form['gender']
      if 'dateOfBirth' in request.form:
        puppyDOB = request.form['dateOfBirth']
      if 'breed' in request.form:
        puppyBreed= request.form['breed']
      if 'weight' in request.json:
        puppyWeight = request.json['weight']
      editedPuppy = session.query(Puppy).filter(and_(Puppy.shelter_id == shelter_id,
      Puppy.id == puppy_id, Puppy.user_id == login_session['user_id'] )).one()
      if editedPuppy:
        if image_src:
          editedPuppy.name = puppyName
          editedPuppy.gender = puppyGender
          editedPuppy.dateOfBirth = puppyDOB
          editedPuppy.breed= puppyBreed
          editedPuppy.weight = puppyWeight
          editedPuppy.owner_id=login_session['user_id']
          if editedPuppy.image_src:
            os.remove(editedPuppy.image_src)
          editedPuppy.image_src = image_src
        else:
          editedPuppy.name = puppyName
          editedPuppy.gender = puppyGender
          editedPuppy.dateOfBirth = puppyDOB
          editedPuppy.breed= puppyBreed
          editedPuppy.weight = puppyWeight
          editedPuppy.owner_id=login_session['user_id']
        session.add(editedPuppy)
        session.commit()
        return jsonify(updated=True, msg='Record updated')
      else:
        return jsonify(updated=False, mesg ='No such record exists')
    except Exception, e:
      print str(e)
      return jsonify(updated=False, masg ='An error occured while trying to update record')
  else:
    return jsonify(updated=False, masg ='Error in request method')



#Delete an puppy
@app.route('/PuppiesShelter/shelter/<int:shelter_id>/puppy/<int:puppy_id>/delete/', methods =['GET','POST'])
@login_required
def deletePuppy(shelter_id, puppy_id):
  if photoToDelete.user_id != login_session['user_id']:
      return ("<script>function myFunction() {alert('You are not authorized "
                "to delete this photo. Please delete from your own "
                " collection.');}</script><body onload='myFunction()'"
                ">")
  if(request.method == 'POST'):
    try:
      puppyToDelete = session.query(Puppy).filter(
        and_(Puppy.shelter_id==shelter_id,
          Puppy.id==puppy_id,
          Puppy.owner_id==login_session['user_id'])).one()
      if puppyToDelete:
        if puppyToDelete.image_src:
          img_src = puppyToDelete.image_src
          session.delete(puppyToDelete)
          session.commit()
        if img_src:
          os.remove(img_src)
        return jsonify(deleted=True, msg ='Record has been deleted')
      else:
        return jsonify(deleted=False, msg ='No record to delete')
    except Exception, e:
      print str(e)
      return jsonify(deleted=False, msg ='An error occured while trying to delete record.')
  else:
    return jsonify(deleted=False, msg ='Error in request method')


if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
