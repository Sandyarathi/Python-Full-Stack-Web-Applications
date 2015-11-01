from sqlalchemy import Column, ForeignKey, Integer, String
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
    imageURL = Column(String(250))


class Collection(Base):
    __tablename__ = 'collection'
    """ Table for movie collections.
    Columns:
        id: Unique collection id.
        name: Name of the collection.
        user_id: user who created the collection.
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    movies = relationship('Movie', cascade = 'delete')

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
            'name': self.name
        }


class Movie(Base):
    __tablename__ = 'movie'
    """ Table for movie information.
    Columns:
        id: Unique movie id.
        name: Movie title.
        director: Movie director
        genre: Movie genre.
        year: Year in which the movie released.
        description: Additional movie information.
        cover_image: filename or external path to the optional album cover image.
        trailer_URL: path to the movie trailer
        user_id: user who created the album.
        collection_id: collections where the album belongs to.
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    director = Column(String(250), nullable=False)
    genre = Column(String(100), nullable=False)
    year = Column(String(4))
    description = Column(String(250))
    cover_image = Column(String(250))
    trailer_URL = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    collection_id = Column(Integer, ForeignKey('collection.id'))
    collection = relationship(Collection)

    # Decorator method
    @property
    def serialize(self):
        """ Selects and formats album data.
        This serializable function will help define what data should be
        send across and put it in a format that Flask can easily use.
        """

        # Returns object data in easily serializable format
        return {
            'id': self.id,
            'name': self.name,
            'director': self.director,
            'genre': self.artist,
            'year': self.year,
            'description': self.description,
            'trailer': self.trailer_URL
        }


engine = create_engine('sqlite:///moviecollections.db')
# Initialize database schema (create tables).
Base.metadata.create_all(engine)