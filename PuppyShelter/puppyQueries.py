from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from puppies_dbSetup import Base, Shelter, Puppy
from datetime import datetime
from datetime import timedelta

engine = create_engine('sqlite:///puppyshelter.db')

Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)

session = DBSession()

#Query all the puppies and return the results in ascending order

def getAllPuppiesInAlphabeticalOrder():
	puppies = session.query(Puppy).order_by(Puppy.name).all()
	print "All puppies in alphabetical order :"
	for puppy in puppies:
		print puppy.id
		print puppy.name
		print puppy.gender
		print puppy.dateOfBirth
		print puppy.breed
		print puppy.picture
		print puppy.shelter_id
		print puppy.weight
		print "\n"

def getPuppiesLessThanSixMonths():
	#sixMonthsAgo = datetime.now() - timedelta(weeks=12)
	#puppies = session.query(Puppy).filter(Puppy.dateOfBirth > sixMonthsAgo).order_by("dateOfBirth desc")
	#print "Puppies less than six months old : "
	shelter = session.query(Shelter).filter_by(id = 1).one()
	puppies = session.query(Puppy).filter_by(shelter_id = 1).all()
	for puppy in puppies:
		print puppy.id
		print puppy.name
		print puppy.gender
		print puppy.dateOfBirth
		print puppy.breed
		print puppy.picture
		print puppy.shelter_id
		print puppy.weight
		print "\n"

def getShelterOccupancies():
	shelters = session.query(Shelter).order_by(Shelter.currentOccupancy).all()
	for shelter in shelters:
		print shelter.name
		print shelter.currentOccupancy
		print "\n"

#getShelterOccupancies()
#getAllPuppiesInAlphabeticalOrder()

getPuppiesLessThanSixMonths()