from sqlalchemy import Table, Column, ForeignKey, Integer, String, Date, Numeric, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy_utils import aggregated
from sqlalchemy import func
 
Base = declarative_base()

# Definition of User Table
class User(Base):
    __tablename__ = 'user'
    """ Table for user information.
    Columns:
        id: Unique user id.
        name: Name of the user.
        email: E-Mail of the user.
        picture: path to profile picture.
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String())

    @property
    def serialize(self):
        return {
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
            'id': self.id
        }
    

# Definition of shelter table
class Shelter(Base):
    __tablename__ = 'shelter'
    """ Table for shelter collections.
    Columns:
        id: Unique collection id.
        name: Name of the collection.

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
    user_id = Column(Integer, ForeignKey('user.id'))
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
            'user_id':self.user_id
            
        }





    
class Puppy(Base):
    __tablename__ = 'puppy'
    """ Table for puppy information.
    Columns:
        id: Unique ppuppy id.
        name: Puppy name.
        shelter_id: Shelter in which Puppy resides.
        picture: filename or external path to the image file.
        owner_id: user who created the collection.
    """
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    gender = Column(String(6), nullable = False)
    dateOfBirth = Column(Date)
    breed = Column(String(250))
    image_src = Column(String)
    shelter_id = Column(Integer, ForeignKey('shelter.id'))
    shelter = relationship(Shelter)
    weight = Column(Numeric(10))
    owner_id=Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

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
            'image_src': self.image_src,
            'shelter':self.shelter.name,
            'owner': self.user.name
            
        }





engine = create_engine('sqlite:///puppyshelter.db')
 

Base.metadata.create_all(engine)