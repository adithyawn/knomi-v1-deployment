from flask import Flask, request, render_template, url_for, redirect, flash

import requests
import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.fields.core import SelectField
from wtforms.validators import length, InputRequired, EqualTo

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, login_required, current_user,logout_user

from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

app = Flask(__name__)


app.config['SECRET_KEY'] = 'ghjdfdsfxxxx'
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://db-droplet1-admin:kicatxxxxx@db-droplet1-do-user-85xxxx-0.b.db.ondigitalocean.com:25060/db-knomi'

db = SQLAlchemy(app)
migrate = Migrate(app,db)
login_manager = LoginManager(app)

#mengarahkan ke def login kalo masuk profile tanpa login
login_manager.login_view = 'login'

######### DATABASE  ###################

#Add User Mixin for Login
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(150))
    status = db.Column(db.Integer)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(150), unique=True)
    answer = db.Column(db.Text)
    category_content = db.Column(db.String(150))
    category_content = db.Column(db.String(150))
    content_date = db.Column(db.DateTime)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), unique=True)


#user_id is default id by login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

######### FORM  ###################

class LoginForm(FlaskForm):
    username = StringField('Username :', validators=[InputRequired(message='Username is required!'), length(max=30, message='Characters can\'t be more than 30!')])
    password = PasswordField('Password :', validators=[InputRequired(message='Password is required!')])
    remember = BooleanField('Remember Me')

class AddUserForm(FlaskForm) :
    name = StringField('Full Name:', validators=[InputRequired(message='Full name is required!'), length(max=100, message='Character can\'t be more than 100!')])
    username = StringField('Username:', validators=[InputRequired(message='Username is required!'), length(max=30, message='Character can\'t be more than 30!')])
    password = PasswordField('Password:', validators=[InputRequired(message='Password is required!'), length(max=150, message='Character can\'t be more than 150'), EqualTo('password_confirm', message='Password must match!')])
    password_confirm = PasswordField('Repeat Password:', validators=[InputRequired(message='Password is required!'), length(max=150, message='Character can\'t be more than 150!'),])
    status = SelectField('status', choices=[(1,"Admin"),(2,"User")])

class AddContentForm(FlaskForm) :
    keywords = StringField('Keyword:', validators=[InputRequired(message='Keyword is required!')])
    answer = TextAreaField('Answer:', validators=[InputRequired(message='Answer is required!')])
    select_category = SelectField('select_category', choices=[])
    select_page = SelectField('page', choices=[(5,5),(10,10)], default=(5,5))


class AddCategoryForm(FlaskForm) :
    category = StringField('Full Name:', validators=[InputRequired(message='Category is required!'), length(max=100, message='Character can\'t be more than 100!')])

###################################

####### #INDEX ############

@app.route('/')
def index():
    form = LoginForm()
       
    return render_template('index.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()

    if request.method == 'POST': #form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # print(user)

        if not user:
            return render_template('index.html', form=form, message='Login Required!')

        if check_password_hash (user.password, form.password.data):
            login_user(user, remember=form.remember.data)

            return redirect(url_for('knowledgebase'))

        return render_template('index.html', form=form, message='Login Failed!')

    return render_template('index.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

####### #SETTINGS ############

@app.route('/settings')
@login_required
def settings():
    form = AddUserForm()
    
    query_user = User.query.all()

    return render_template('settings.html', form=form, query_user=query_user)

@app.route('/adduser', methods=['GET','POST'])
@login_required
def adduser():
    form = AddUserForm()
    #this is for query in render template 
    query_user = User.query.all()

    if form.validate_on_submit():
        try :
            new_user = User(name=form.name.data, username=form.username.data, password=generate_password_hash(form.password.data), status=form.status.data)
            db.session.add(new_user)
            db.session.commit()
            flash('User successfully added !','success')
        except IntegrityError :
            db.session.rollback()
            flash('Username is duplicated !','danger')
        
        return redirect(url_for('settings'))
    else :
        flash('Add user error !','danger')

    return render_template('settings.html', form=form, query_user=query_user)

@app.route('/deleteuser/<int:id>', methods=['GET','POST'])
@login_required
def deleteuser(id):
    query_id = User.query.filter_by(id=id).first()
    db.session.delete(query_id)
    db.session.commit()

    return redirect(url_for('settings'))

@app.route('/edituser/<int:id>', methods=['GET'])
@login_required
def edituser(id):
    form = AddUserForm()
    query_user = User.query.all()
    
    query_edit_by_id = User.query.filter_by(id=id).first()
    # print(query_edit_by_id.name)
    # print(type(query_edit_by_id))

    #untuk edit form ketika render template dengan query sesuai id-nya
    form.name.data = query_edit_by_id.name
    form.username.data = query_edit_by_id.username
    # form.status.data = query_id.status

    return render_template('settings.html', form=form, query_user=query_user) #query user biar muncul semua di list template settings.html


####### #KNOWLEDGEBASE ############

@app.route('/knowledgebase', methods=['GET','POST'], defaults={"page":1})
@app.route('/knowledgebase/<int:page>',methods=['GET','POST'])
@login_required
def knowledgebase(page):

    form = AddContentForm()

    page = page
    pages = 5
        

    # source = [('mangga',),('apel',),('jeruk',)] convert to List
    query_keyword = Content.query.with_entities(Content.keyword).all()
    source = [j for i in query_keyword for j in i]
    # print((source))

    contents = Content.query.order_by(Content.content_date.desc()).paginate(page,pages,error_out=False)

    # source = [j for i in query_keyword for j in i]
    # print((source))
    query_category = Category.query.with_entities(Category.category).all()
    query_category = [j for i in query_category for j in i]

    form.select_category.choices = query_category

    update_answer = 0

    if request.method == 'POST':
        page = 5
        pages = contents.total

        if request.form.get('tag-all') :
        # tag = request.form['tag-all'] #kalau mau langsung ambil datanya pakai ['tag'] bukan request.form.tag atau bisa pakai form.tag.data kalau pakai wtforms
            tag = request.form.get('tag-all')
            search = "%{}%".format(tag)
            contents = Content.query.filter(or_(Content.keyword.like(search),Content.answer.like(search))).paginate(per_page=pages,error_out=True)

        elif request.form.get('tag-keyword') :
            tag = request.form.get('tag-keyword')
            search = "%{}%".format(tag)
            contents = Content.query.filter(Content.keyword.like(search)).paginate(per_page=pages,error_out=True)

        elif request.form.get('tag-answer') :
            tag = request.form.get('tag-answer')
            search = "%{}%".format(tag)
            contents = Content.query.filter(Content.answer.like(search)).paginate(per_page=pages,error_out=True)

        elif request.form.get('select_category') :

            search = request.form.get('select_category')
            contents = Content.query.filter(Content.category_content.like(search)).paginate(per_page=pages,error_out=True)

    return render_template('knowledgebase.html',current_user=current_user, source=source, contents=contents, form=form, update_answer=update_answer)
    
@app.route('/addcontent', methods=['POST'])
@login_required
def addcontent():

    form = AddContentForm()

    if request.method == 'POST':
        
        getkeywords = request.form.get('keywords')
        getkeywordssplit = getkeywords.split(",")
        # output = ['konten',' konten update',' konten update mingguan']
        # BUT there is space lead ' konten update'

        keywords = []
        for i in getkeywordssplit:
            print(i)
            s = i.lstrip()
            keywords.append(s)
        # output = ['konten','konten update','konten update mingguan']

        for i in keywords:
            answer = form.answer.data
            category_content = form.select_category.data
            try :
                addcontent = Content(keyword=i, answer=answer, category_content=category_content, content_date=datetime.now())
                db.session.add(addcontent)
                db.session.commit()
                flash("Keyword '{}' is succesfully added!".format(i),"success")
            except IntegrityError :
                db.session.rollback()
                flash("Keyword '{}' is available, you can't duplicate!".format(i),"danger")
                                   
    return redirect(url_for('knowledgebase'))

@app.route('/updatecontent', methods=['POST'])
@login_required
def updatecontent():

    form = AddContentForm()

    query_contents = Content.query.filter_by(keyword=form.keywords.data).first()
    if request.method == 'POST':
        
        query_contents.answer = form.answer.data
        query_contents.category_content = form.select_category.data
        db.session.commit()
        flash("Keyword '{}' is updated".format(form.keywords.data),"success")
                                   
    return redirect(url_for('knowledgebase'))

@app.route('/deletecontent/<int:id>', methods=['GET','POST'])
@login_required
def deletecontent(id):
    contents = Content.query.filter_by(id=id).first()
    db.session.delete(contents)
    db.session.commit()

    return redirect(url_for('knowledgebase'))

@app.route('/deletecontentselected', methods=['POST'])
@login_required
def deletecontentselected():

    if request.method == 'POST':
        selectedcontents = request.form.getlist('selectedcheckbox')
        # print(selectedcontents)
        for i in selectedcontents:
            contentselected = Content.query.filter_by(id=i).first()
            db.session.delete(contentselected)
            db.session.commit()

    return redirect(url_for('knowledgebase'))

@app.route('/editcontent/', methods=['GET','POST'], defaults={"page":1}) #pg
@app.route('/editcontent/<int:page>/<int:id>', methods=['GET','POST'])
@login_required
def editcontent(page,id): #pg

    form = AddContentForm()

    page = page #pg
    pages = 5 #pg

    query_keyword = Content.query.with_entities(Content.keyword).all()
    source = [j for i in query_keyword for j in i]
    # print((source))

    query_category = Category.query.with_entities(Category.category).all()
    query_category = [j for i in query_category for j in i]

    contents = Content.query.order_by(Content.content_date.desc()).paginate(page,pages,error_out=False) #pg
    
    contents_edit_by_id = Content.query.filter_by(id=id).first()
    form.keywords.data = contents_edit_by_id.keyword
    form.answer.data = contents_edit_by_id.answer
    #to give dropdown list option
    form.select_category.choices = query_category
    #to input default value from query
    form.select_category.data = contents_edit_by_id.category_content

    update_answer = 1

    return render_template('knowledgebase.html', contents=contents, form=form,source=source, update_answer=update_answer) #query user biar muncul semua di list template settings.html

####### #CATEGORY ############

@app.route('/category')
@login_required
def category():
    form = AddCategoryForm()

    query_category = Category.query.all()
    
    return render_template('category.html', form=form, query_category=query_category, list_category=query_category)

@app.route('/addcategory', methods=['GET','POST'])
@login_required
def addcategory():
    form = AddCategoryForm()
    #this is for query in render template 
    query_category = Category.query.all()

    if form.validate_on_submit():
        try :
            new_category = Category(category=form.category.data)
            db.session.add(new_category)
            db.session.commit()
            flash('Category successfully added !','success')
        except IntegrityError :
            db.session.rollback()
            flash('Category is duplicated !','danger')
        
        return redirect(url_for('category'))
    else :
        flash('Add user error !','danger')

    return render_template('category.html', form=form, query_category=query_category)

@app.route('/deletecategory/<int:id>', methods=['GET','POST'])
@login_required
def deletecategory(id):
    query_id = Category.query.filter_by(id=id).first()
    db.session.delete(query_id)
    db.session.commit()

    return redirect(url_for('category'))

@app.route('/editcategory/<int:id>', methods=['GET'])
@login_required
def editcategory(id):
    form = AddCategoryForm()
    query_category = Category.query.all()
    
    query_edit_by_id = Category.query.filter_by(id=id).first()

    form.category.data = query_edit_by_id.category

    return render_template('category.html', form=form, query_category=query_category) #query category biar muncul semua di list template category.html

@app.route('/webhook', methods=['POST'])
def webhook():

    r = request.form['data']
    j = eval(r)

    print(j)

    ask = j['text'].lower()

    # query_answer = Content.query.filter_by(keyword=ask).all()

    query_keyword = Content.query.with_entities(Content.keyword).all()
    # output = [('konten',),('konten update',),('konten update mingguan',)]
    source = [j for i in query_keyword for j in i]
    # output = ['konten','konten update','konten update mingguan']

    if ask in source:
        check_answer = Content.query.filter(Content.keyword.like(ask)).all()
 
        for i in check_answer:
            reply = i.answer

    else :
        default_answer = Content.query.filter(Content.keyword.like('defaultanswer')).all()
 
        for i in default_answer:
            reply = i.answer

    return {'autoreply':reply}

if __name__ == '__main__':
    app.run(debug=True)
