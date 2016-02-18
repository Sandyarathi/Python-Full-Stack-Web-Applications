from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item


#Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Show catalog home page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
  categories = session.query(Category).order_by(asc(Category.name))
  items = session.query(Item).order_by(asc(Item.created_date))
  return render_template('catalog.html', categories=categories, items = items)


#JSON APIs to Show a category items
@app.route('/catalog/category/<int:category_id>/')
@app.route('/catalog/category/<int:category_id>/items/JSON')
def showCategoryAllItemsJSON(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return render_template('viewCategoryItems.html', category=category, items= items)
    #return jsonify(Items=[i.serialize for i in items])

#View a item description
@app.route('/catalog/category/<int:category_id>/item/<int:item_id>/')
@app.route('/catalog/category/<int:category_id>/item/<int:item_id>/description/')
def showItemDescription(category_id,item_id):
  item = session.query(Item).filter_by(id = item_id).one()
  return render_template('viewItemDescription.html', item=item)


#Create a new category
@app.route('/catalog/category/new/', methods = ['GET', 'POST'])
def newCategory():
  if request.method == 'POST':
    newCat = Category(name = request.form['name'])
    session.add(newCat)
    session.commit()
    flash("New Category Added!")
    return redirect(url_for('showCatalog'))
  else:
    return render_template('newCategory.html')

#Edit a category
@app.route('/catalog/category/<int:category_id>/edit/', methods=['GET','POST'])
def editCategory(category_id):
  editedCategory = session.query(Category).filter_by(id = category_id).one()
  if request.method == 'POST':
    if request.form['name']:
      editedCategory.name = request.form['name']
    session.add(editedCategory)
    session.commit()
    return redirect(url_for('showCatalog'))
  else:
    return render_template('editCategory.html', c=editedCategory)

#Delete a category
@app.route('/catalog/category/<int:category_id>/delete/', methods = ['GET','POST'])
def deleteCategory(category_id):
  catToDelete = session.query(Category).filter_by(id=category_id).one()
  if request.method == 'POST':
    session.delete(catToDelete)
    session.commit()
    return redirect(url_for('showCatalog'))
  else:
    return render_template('deleteCategory.html', category=catToDelete)

#Create a new item
@app.route('/catalog/category/<int:category_id>/item/new/', methods = ['GET','POST'])
def newItem(category_id):
  if(request.method == 'POST'):
    newItem = Item(name = request.form['name'],
      description = request.form['description'],
      imageURL = request.form['imageURL'],
      category_id=category_id)
    session.add(newItem)
    session.commit()
    return redirect(url_for('showCategoryAllItems', category_id= category_id))
  else:
    return render_template('newItem.html', category_id=category_id)


#Edit an item
@app.route('/catalog/category/<int:category_id>/item/<int:item_id>/edit/', methods =['GET','POST'])
def editItem(category_id,item_id):
  editedItem = session.query(Item).filter_by(id=item_id).one()
  if(request.method == 'POST'):
    if request.form['name']:
      editedItem.name = request.form['name']
    if request.form['description']:
      editedItem.description= request.form['description']
    if request.form['imageURL']:
      editedItem.imageURL = request.form['imageURL']
    session.add(editedItem)
    session.commit()
    return redirect(url_for('showItemDescription', category_id=category_id, item_id= item_id))
  else:
    return render_template(
      'editItem.html', category_id=category_id, item_id=item_id, item=editedItem)

#Delete an item
@app.route('/catalog/category/<int:category_id>/item/<int:item_id>/delete/', methods =['GET','POST'])
def deleteItem(category_id, item_id):
  itemToDelete = session.query(Item).filter_by(id=item_id).one()
  if request.method == 'POST':
      session.delete(itemToDelete)
      session.commit()
      return redirect(url_for('showCategoryAllItems', category_id=category_id))
  else:
      return render_template('deleteItem.html', item=itemToDelete)






    










if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
