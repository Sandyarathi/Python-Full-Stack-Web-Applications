from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from Albumsdatabase_setup import Album, Base, Photo, User
 
engine = create_engine('sqlite:///PhotoCollections.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

fake_user = User(name = "Sandyarathi", email = "sandyasoumya@gmail.com", imageURL = "https://www.facebook.com/photo.php?fbid=512387765601281&set=a.104421169731278.8509.100004901858250&type=3&theater")

album1 = Album(name = "Yosemite", user = fake_user)
session.add(album1)
session.commit()

album2 = Album(name = "Mount Shastha", user = fake_user)
session.add(album2)
session.commit()


photo1 = Photo(name = "Mariposa Grove",
	year = "2014",
	location = "Yosemite",
	description = "Mariposa Grove during Yosemite trip",
	image ='https://www.natureflip.com/sites/default/files/photo/yosemite-national-park/yosemite-national-park-mariposa-grove-redwoods.jpg',
	user = fake_user,
	album = album1)
session.add(photo1)
session.commit()

photo2 = Photo(name = "Tunnel view",
	year = "2014",
	location = "Yosemite",
	description = "Tunnel view during Yosemite trip",
	image ='https://upload.wikimedia.org/wikipedia/commons/e/ec/1_yosemite_valley_tunnel_view_2010.JPG',
	user = fake_user,
	album = album1)
session.add(photo2)
session.commit()

photo3 = Photo(name = "Lake Siskiyou",
	year = "2014",
	location = "MtShastha",
	description = "Lake siskiyou resort",
	image ='http://media-cdn.tripadvisor.com/media/photo-s/01/99/54/62/plenty-for-kids-to-do.jpg',
	user = fake_user,
	album = album2)
session.add(photo3)
session.commit()



print "added photo albums!"

