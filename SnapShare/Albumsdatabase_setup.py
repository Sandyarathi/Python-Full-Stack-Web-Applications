from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

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

class Album(Base):
    __tablename__ = 'album'
    """ Table for photo collections.
    Columns:
        id: Unique collection id.
        name: Name of the collection.
        user_id: user who created the collection.
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    photos = relationship('Photo', cascade = 'delete')

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
            'user': self.user_id
        }


class Photo(Base):
    __tablename__ = 'photo'
    """ Table for photo information.
    Columns:
        id: Unique photo id.
        name: Photo title.
        year: Year in which the photo was shared.
        location: Location where the photo was taken.
        description: Additional photo information.
        created_on:Image upload date
        edited_on:Image edit date
        image: filename or external path to the image file.
        user_id: user who uploaded the photo.
        album_id : album name it belongs to
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    year = Column(String(4))
    location = Column(String(250))
    description = Column(String(250))
    image = Column(String(250))
    created_on:Column(TIMESTAMP)
    edited_on:Column(TIMESTAMP)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    album_id = Column(Integer, ForeignKey('album.id'))
    album = relationship(Album)

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
            'year': self.year,
            'location': self.location,
            'description': self.description,
            'image': self.image,
            'created_on':self.created_on,
            'edited_on':self.edited_on,
            'owner':self.user_id,
            'album':self.album_id
            
        }


engine = create_engine('sqlite:///PhotoCollections.db')
# Initialize database schema (create tables).
Base.metadata.create_all(engine)