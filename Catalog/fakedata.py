from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Category, Base, Item
 
engine = create_engine('sqlite:///catalog.db')
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

category1 = Category(name = "Sports & Outdoors")
session.add(category1)
session.commit()


item1 = Item(name = "Golf Club", description = "Callaway Strata 12-Piece Set", imageURL ='http://ecx.images-amazon.com/images/I/61I9UWZocoL._SL1500_.jpg', category = category1)
session.add(item1)
session.commit()

item2 = Item(name = "Golf Ball", description = "Wilson Titanium Balls", imageURL = 'http://ecx.images-amazon.com/images/I/51GwIc71MhL.jpg', category = category1)
session.add(item2)
session.commit()

item3 = Item(name = "Yoga Mat", description = "Sivan Health and Fitness 1/2-Inch Extra Thick 71-Inch Long NBR Comfort Foam Yoga Mat", imageURL = 'http://ecx.images-amazon.com/images/I/91Ja6q43RSL._SL1500_.jpg', category = category1)
session.add(item3)
session.commit()


category2 = Category(name = "Electronics")
session.add(category2)
session.commit()

item4 = Item(name = "LCD TV", description = "VIZIO E32-C1 32-Inch 1080p Smart LED HDTV", imageURL = 'http://ecx.images-amazon.com/images/I/819nCWkn%2BEL._SL1500_.jpg', category = category2)
session.add(item4)
session.commit()

item5 = Item(name = "Bluetooth speaker", description = "DKnight Magicbox Ultra-Portable Wireless Bluetooth Speaker", imageURL = 'http://ecx.images-amazon.com/images/I/818V5qyHUzL._SL1500_.jpg', category = category2)
session.add(item5)
session.commit()

item6 = Item(name = "Printer", description = "Brother HL-L2300D Monochrome Laser Printer", imageURL = 'http://ecx.images-amazon.com/images/I/31s7K%2BFEPAL.jpg', category = category2)
session.add(item6)
session.commit()






print "added data items!"

