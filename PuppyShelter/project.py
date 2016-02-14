from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)


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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "PuppiesShelter"

#Connect to Database and create database session
engine = create_engine('sqlite:///puppyshelter.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
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

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    newUser = User(name= login_session['username'], email= login_session['email'],imageURL =login_session['picture'])
    session.add(newUser)
    session.commit()
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
      return redirect(url_for('showCatalog'))
    return func(*args, **kwargs)
  return function_wrapper


# To show home page shelters & puppies
@app.route('/PuppiesShelter', methods = ['GET'])
@app.route('/PuppiesShelter/catalog/', methods = ['GET'])
def showCatalog():
  print "in show catalog"
  shelters = session.query(Shelter).order_by(asc(Shelter.name))
  sixMonthsAgo = datetime.now() - timedelta(weeks=12)
  puppies = session.query(Puppy).filter(Puppy.dateOfBirth > sixMonthsAgo).order_by("dateOfBirth desc")
  #return render_template('catalog.html', shelters=shelters, puppies = puppies)
  return jsonify(Shelters =[a.serialize for a in shelters], Puppies = [p.serialize for p in puppies])

#To Show a shelter
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/',methods = ['GET'])
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/puppies/', methods = ['GET'])
def showShelterAllPuppies(shelter_id):
    shelter = session.query(Shelter).filter_by(id = shelter_id).one()
    puppies = session.query(Puppy).filter_by(shelter_id = shelter_id).all()
    #return render_template('viewShelterPuppys.html', shelter=shelter, puppies= puppies)
    return jsonify(Puppies=[i.serialize for i in puppies])

#View a puppy description
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/puppy/<int:puppy_id>/', methods = ['GET'])
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/puppy/<int:puppy_id>/description/', methods = ['GET'])
def showPuppyDescription(shelter_id,puppy_id):
  puppy = session.query(Puppy).filter_by(id = puppy_id).one()
  #return render_template('viewPuppyDescription.html', puppy=puppy)
  return jsonify(Puppy = puppy.serialize)


#Create a new shelter
@app.route('/PuppiesShelter/catalog/shelter/new/', methods = ['POST'])
@login_required
def newShelter():
  if request.method == 'POST':
    if not ('name' in request.json):
      response = jsonify({'result': 'ERROR'})
      response.status_code = 400
      return response
    else:
      newCol = Shelter(name= request.json['name'],
        address = request.json['address'],
        city = request.json['city'],
        state = request.json['state'],
        zipCode = request.json['zipCode'],
        website = request.json['website'],
        maxCapacity = request.json['maxCapacity'],
        owner_id=login_session['user_id'])
      session.add(newCol)
      session.commit()
      flash("New Shelter Added!")
      return jsonify(NewShelter = newCol.serialize)

#Edit a shelter
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/edit/', methods=['GET','POST'])
@login_required
def editShelter(shelter_id):
  editedShelter = session.query(Shelter).filter_by(id = shelter_id).one()
  if editedShelter.owner_id != login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
                "to edit this collection.');}</script><body onload='myFunction()'>")
  if request.method == 'POST':
    if ('name' in request.json):
      editedShelter.name = request.json['name']
    if('address' in request.json):
      editedShelter.address = request.json['address']
    if('city' in request.json):
      editedShelter.city = request.json['city']
    if('state' in request.json):
      editedShelter.state = request.json['state']
    if('zipCode' in request.json):
      editedShelter.zipCode = request.json['zipCode']
    if('website' in request.json):
      editedShelter.website = request.json['website']
    if('maxCapacity' in request.json):
      editedShelter.maxCapacity = request.json['maxCapacity']
    session.add(editedShelter)
    session.commit()
    return jsonify(EditedShelter = editedShelter.serialize)

#Delete a shelter
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/delete/', methods = ['GET','POST'])
@login_required
def deleteShelter(shelter_id):
  colToDelete = session.query(Shelter).filter_by(id=shelter_id).one()
  if editedShelter.owner_id != login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
                "to edit this collection.');}</script><body onload='myFunction()'>")
  if request.method == 'POST':
    session.delete(colToDelete)
    session.commit()
    return jsonify(DeletedShelter = colToDelete.serialize)

#Create a new puppy
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/puppy/new/', methods = ['GET','POST'])
@login_required
def newPuppy(shelter_id):
  if 'username' not in login_session:
        return redirect('/PuppiesShelter/login')
  if(request.method == 'POST'):
    newPuppy = Puppy(name = request.json['name'],
      gender = request.json['gender'],
      dateOfBirth = request.json['dateOfBirth'],
      breed = request.json['breed'],
      picture = request.json['picture'],
      shelter_id=shelter_id,
      weight=request.json['weight'])
    session.add(newPuppy)
    session.commit()
    return jsonify(NewPuppy = newPuppy.serialize)

#Edit an puppy
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/puppy/<int:puppy_id>/edit/', methods =['GET','POST'])
@login_required
def editPuppy(shelter_id,puppy_id):
  editedPuppy = session.query(Puppy).filter_by(id=puppy_id).one()
  shelter = session.query(Shelter).filter_by(id=shelter_id).one()
  if shelter.owner_id!= login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
                "to edit this record.');}</script><body onload='myFunction()'>")
  if(request.method == 'POST'):
    if 'name' in request.json:
      editedPuppy.name = request.json['name']
    if 'gender' in request.json:
      editedPuppy.gender = request.json['gender']
    if 'dateOfBirth' in request.json:
      editedPuppy.dateOfBirth = request.json['dateOfBirth']
    if 'breed' in request.json:
      editedPuppy.breed= request.json['breed']
    if 'picture' in request.json:
      editedPuppy.picture = request.json['picture']
    if 'weight' in request.json:
      editedPuppy.weight = request.json['weight']
    session.add(editedPuppy)
    session.commit()
    return jsonify(EditedPuppy = editedPuppy.serialize)

#Delete an puppy
@app.route('/PuppiesShelter/catalog/shelter/<int:shelter_id>/puppy/<int:puppy_id>/delete/', methods =['GET','POST'])
@login_required
def deletePuppy(shelter_id, puppy_id):
  puppyToDelete = session.query(Puppy).filter_by(id=puppy_id).one()
  shelter = session.query(Shelter).filter_by(id=shelter_id).one()
  if shelter.owner_id!= login_session['user_id']:
    return ("<script>function myFunction() {alert('You are not authorized "
                "to delete this record.');}</script><body onload='myFunction()'>")
  if request.method == 'POST':
      session.delete(puppyToDelete)
      session.commit()
      return jsonify(DeletedPuppy = puppyToDelete.serialize)




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
