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
	location = "Yosemite"
	description = "Mariposa Grove during Yosemite trip",
	image ='https://www.natureflip.com/sites/default/files/photo/yosemite-national-park/yosemite-national-park-mariposa-grove-redwoods.jpg',
	user = fake_user,
	album = album1)
session.add(photo1)
session.commit()

photo1 = Photo(name = "Mariposa Grove",
	year = "2014",
	location = "Yosemite"
	description = "Mariposa Grove during Yosemite trip",
	image ='https://www.natureflip.com/sites/default/files/photo/yosemite-national-park/yosemite-national-park-mariposa-grove-redwoods.jpg',
	user = fake_user,
	album = album1)
session.add(photo1)
session.commit()

photo3 = Photo(name = "The Imitation Game",
	director = "Morten Tyldum",
	genre = "Thriller/Drama",
	year = "2015",
	description = "In 1939, newly created British intelligence agency MI6 recruits Cambridge mathematics alumnus Alan Turing (Benedict Cumberbatch) to crack Nazi codes, including Enigma -- which cryptanalysts had thought unbreakable. ",
	cover_image ='http://t0.gstatic.com/images?q=tbn:ANd9GcQQ5vi9xgRkP0nk5aRn8tcGEGRnOQyM-aAS1ldqfQSi_69V1yfU',
	trailer_URL = "https://www.youtube.com/watch?v=S5CjKEFb-sM",
	user = fake_user,
	album = album1)
session.add(photo3)
session.commit()

photo4 = Photo(name = "Listen Amaya",
	director = "Avinash Kumar Singh",
	genre = "Drama",
	year = "2013",
	description = "Listen... Amaya is 2013 Hindi drama film directed by Avinash Kumar Singh, and starring Farooq Shaikh, Deepti Naval and Swara Bhaskar as leads.",
	cover_image ='http://t3.gstatic.com/images?q=tbn:ANd9GcQID0pAHlSkswJk_0MQhQLD-I7zbkWUVcL5YrkL21Dm6p2oIZPu',
	trailer_URL = "www.youtube.com/watch?v=RY4xXvvHcdE",
	user = fake_user,
	album = album2)
session.add(photo4)
session.commit()

photo5 = Photo(name = "Black",
	director = "Sanjay Leela Bhansali",
	genre = "Drama/Family",
	year = "2005",
	description = "Paul (Dhritiman Chaterji) and Catherine McNally (Shernaz Patel) give birth to their first daughter, Michelle (Rani Mukherji), who can neither hear nor see. ",
	cover_image ='http://img.hindilinks4u.to/2007/06/Black-2005.jpg',
	trailer_URL = "https://www.youtube.com/watch?v=Smd_xZHCCzI",
	user = fake_user,
	album = album2)
session.add(photo5)
session.commit()

photo6 = Photo(name = "Slumdog Millionaire",
	director = "Danny Boyle",
	genre = "Drama/Crime",
	year = "2008",
	description = "As 18-year-old Jamal Malik (Dev Patel) answers questions on the Indian version of /'Who Wants to Be a Millionaire,/' flashbacks show how he got there.",
	cover_image ='https://upload.wikimedia.org/wikipedia/en/f/fe/Slumdog_millionaire_ver2.jpg',
	trailer_URL = "https://www.youtube.com/watch?v=AIzbwV7on6Q",
	user = fake_user,
	album = album2)
session.add(photo6)
session.commit()




print "added photo albums!"

