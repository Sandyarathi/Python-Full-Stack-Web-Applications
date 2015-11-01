from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from Moviesdatabase_setup import Base, Collection, Movie


#Connect to Database and create database session
engine = create_engine('sqlite:///moviecollections.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Show catalog home page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
  collections = session.query(Collection).order_by(asc(Collection.name))
  movies = session.query(Movie).order_by(asc(Movie.year))
  return render_template('catalog.html', collections=collections, movies = movies)


#To Show a collection movies
@app.route('/catalog/collection/<int:collection_id>/')
@app.route('/catalog/collection/<int:collection_id>/movies/')
def showCollectionAllMovies(collection_id):
    collection = session.query(Collection).filter_by(id = collection_id).one()
    movies = session.query(Movie).filter_by(collection_id = collection_id).all()
    return render_template('viewCollectionMovies.html', collection=collection, movies= movies)
    #return jsonify(Movies=[i.serialize for i in movies])

#View a movie description
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/')
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/description/')
def showMovieDescription(collection_id,movie_id):
  movie = session.query(Movie).filter_by(id = movie_id).one()
  return render_template('viewMovieDescription.html', movie=movie)


#Create a new collection
@app.route('/catalog/collection/new/', methods = ['GET', 'POST'])
def newCollection():
  if request.method == 'POST':
    newCat = Collection(name = request.form['name'])
    session.add(newCat)
    session.commit()
    flash("New Collection Added!")
    return redirect(url_for('showCatalog'))
  else:
    return render_template('newCollection.html')

#Edit a collection
@app.route('/catalog/collection/<int:collection_id>/edit/', methods=['GET','POST'])
def editCollection(collection_id):
  editedCollection = session.query(Collection).filter_by(id = collection_id).one()
  if request.method == 'POST':
    if request.form['name']:
      editedCollection.name = request.form['name']
    session.add(editedCollection)
    session.commit()
    return redirect(url_for('showCatalog'))
  else:
    return render_template('editCollection.html', c=editedCollection)

#Delete a collection
@app.route('/catalog/collection/<int:collection_id>/delete/', methods = ['GET','POST'])
def deleteCollection(collection_id):
  catToDelete = session.query(Collection).filter_by(id=collection_id).one()
  if request.method == 'POST':
    session.delete(catToDelete)
    session.commit()
    return redirect(url_for('showCatalog'))
  else:
    return render_template('deleteCollection.html', collection=catToDelete)

#Create a new movie
@app.route('/catalog/collection/<int:collection_id>/movie/new/', methods = ['GET','POST'])
def newMovie(collection_id):
  if(request.method == 'POST'):
    newMovie = Movie(name = request.form['name'],
      director = request.form['director'],
      genre = request.form['genre'],
      year = request.form['year'],
      description = request.form['description'],
      cover_image = request.form['cover_image'],
      trailer_URL = request.form['trailer_URL'],
      collection_id=collection_id)
    session.add(newMovie)
    session.commit()
    return redirect(url_for('showCollectionAllMovies', collection_id= collection_id))
  else:
    return render_template('newMovie.html', collection_id=collection_id)


#Edit an movie
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/edit/', methods =['GET','POST'])
def editMovie(collection_id,movie_id):
  editedMovie = session.query(Movie).filter_by(id=movie_id).one()
  if(request.method == 'POST'):
    if request.form['name']:
      editedMovie.name = request.form['name']
    if request.form['director']:
      editedMovie.director = request.form['director']
    if request.form['genre']:
      editedMovie.genre = request.form['genre']
    if request.form['year']:
      editedMovie.year = request.form['year']
    if request.form['description']:
      editedMovie.description= request.form['description']
    if request.form['cover_image']:
      editedMovie.cover_image = request.form['cover_image']
    if request.form['trailer_URL']:
      editedMovie.trailer_URL= request.form['trailer_URL']
    session.add(editedMovie)
    session.commit()
    return redirect(url_for('showMovieDescription', collection_id=collection_id, movie_id= movie_id))
  else:
    return render_template(
      'editMovie.html', collection_id=collection_id, movie_id=movie_id, movie=editedMovie)

#Delete an movie
@app.route('/catalog/collection/<int:collection_id>/movie/<int:movie_id>/delete/', methods =['GET','POST'])
def deleteMovie(collection_id, movie_id):
  movieToDelete = session.query(Movie).filter_by(id=movie_id).one()
  if request.method == 'POST':
      session.delete(movieToDelete)
      session.commit()
      return redirect(url_for('showCollectionAllMovies', collection_id=collection_id))
  else:
      return render_template('deleteMovie.html', movie=movieToDelete)






    










if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
