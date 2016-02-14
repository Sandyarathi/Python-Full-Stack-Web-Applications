from sqlalchemy import Table, Column, ForeignKey, Integer, String, Date, Numeric, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy_utils import aggregated
from sqlalchemy import func
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    """ Table for user information.
    Columns:
        id: Unique user id.
        name: Name of the user.
        email: E-Mail of the user.
        imageURL: path to profile picture.
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    imageURL = Column(String())

PuppyAdopter = Table('PuppyAdopter', Base.metadata,
    Column('puppyId', Integer(), ForeignKey('puppy.id')),
    Column('adopterId', Integer(), ForeignKey('adopter.id')))


class Shelter(Base):
    __tablename__ = 'shelter'
    """ Table for shelter collections.
    Columns:
        id: Unique collection id.
        name: Name of the collection.
        owner_id: user who created the collection.

    """
    id = Column(Integer, primary_key = True)
    name =Column(String(80), nullable = False)
    address = Column(String(250))
    city = Column(String(80))
    state = Column(String(20))
    zipCode = Column(String(10))
    website = Column(String)
    maxCapacity = Column(Integer)
    @aggregated('puppies', Column(Integer))
    def currentOccupancy(self):
        return func.count('1')
    puppies = relationship('Puppy', backref = 'shelterPuppies', cascade = 'delete')
    owner_id=Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Decorator method
    @property
    def serialize(self):
        """ Selects and formats collection data.
        This serializable function will help define what data should be
        send across and put it in a format that Flask can easily use.
        """
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'website': self.website,
            'currentOccupancy': self.currentOccupancy,
            'owner': self.user.name
        }





    
class Puppy(Base):
    __tablename__ = 'puppy'
    """ Table for puppy information.
    Columns:
        id: Unique ppuppy id.
        name: Puppy name.
        shelter_id: Shelter in which Puppy resides.
        picture: filename or external path to the image file.
    """
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    gender = Column(String(6), nullable = False)
    dateOfBirth = Column(Date)
    breed = Column(String(250))
    picture = Column(String)
    shelter_id = Column(Integer, ForeignKey('shelter.id'))
    shelter = relationship(Shelter)
    weight = Column(Numeric(10))
    adopters = relationship('Adopter', secondary = PuppyAdopter, backref = 'puppies')

     # Decorator method
    @property
    def serialize(self):
        """ Selects and formats photo data.
        This serializable function will help define what data should be
        send across and put it in a format that Flask can easily use.
        """

        # Returns object data in easily serializable format
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'dateOfBirth': str(self.dateOfBirth),
            'breed': self.breed,
            'picture': self.picture,
            'shelter':self.shelter.name
            
        }


class Adopter(Base):
    __tablename__ = 'adopter'
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False)
    address = Column(String(250))
    city = Column(String(80))
    state = Column(String(20))
    zipCode = Column(String(10))
    

class PuppyProfile(Base):
    __tablename__ = 'puppy_profile'
    id = Column(Integer, primary_key = True)
    puppy_id = Column(Integer, ForeignKey('puppy.id'))
    picture = Column(String)
    description = Column(String)
    puppy = relationship(Puppy)




engine = create_engine('sqlite:///puppyshelter.db', echo=True)
 

Base.metadata.create_all(engine)