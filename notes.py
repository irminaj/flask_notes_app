import os

from flask import Flask, render_template, flash, url_for, redirect, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms.widgets import TextArea
import email_validator
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'SRKyycK9I35J1qzxPbKleSdDc4PreDlP'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(
    basedir, "data.sqlite"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegistrationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Length(1, 64), Email(email_validator)])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2', message="Passwords didn't match")])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()]) 
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = StringField('Content', validators=[DataRequired()], widget=TextArea())
    category = SelectField('Category', choices=[])
    submit = SubmitField('Create')

class CategoryForm(FlaskForm):
    name = StringField('Category name', validators=[DataRequired()])
    submit = SubmitField('Create')

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    notes = db.relationship('Note', backref='user')

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username


class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(500))
    content = db.Column(db.String(10000))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    def __repr__(self):
        return '<Note %r>' % self.title

### Problema cia ####

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), unique=True)
    notes = db.relationship('Note')

    def __repr__(self):
        return self.name


@app.route('/', methods=['GET', 'POST'])
def show_notes():
    notes = Note.query.all()
    return render_template('notes.html', notes=notes)

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    notes = Note.query.all()
    return render_template('notes.html', notes=notes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now login.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('notes')
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/add_note', methods=['GET', 'POST'])
@login_required
def add_note():
    categories = db.session.query(Category).all()
    categories_list = [(categ.id, categ.name) for categ in categories]
    form = NoteForm()
    form.category.choices = categories_list
    if form.validate_on_submit():
        selected_category_id = int(form.category.data[0])
        note = Note(title=form.title.data, content=form.content.data, user_id=current_user.id, category_id=selected_category_id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('notes'))
    else:
        flash('You need to login')
    return render_template('add_note.html', form=form)

@app.route('/notes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    categories = db.session.query(Category).all()
    categories_list = [(categ.id, categ.name) for categ in categories]
    note = Note.query.get_or_404(id)
    form = NoteForm()
    form.category.choices = categories_list
    if form.validate_on_submit():
        selected_category_id = int(form.category.data[0])
        note.title = form.title.data
        note.content = form.content.data
        note.category_id = selected_category_id
        db.session.add(note)
        db.session.commit()
        flash('The note has been updated')
        return redirect(url_for('.notes', id=note.id))
    if current_user.id == note.user_id:
        form.title.data = note.title
        form.content.data = note.content
        selected_category_id = note.category_id
        return render_template('edit_note.html', form=form)
    else:
        flash("You don't have a permission to edit this note")
        notes = Note.query.all()
        return render_template('notes.html', notes=notes)

@app.route('/notes/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_note(id):
    note_to_delete = Note.query.get_or_404(id)
    id = current_user.id
    if id == note_to_delete.user_id:
        try:
            db.session.delete(note_to_delete)
            db.session.commit()
            flash('Note was deleted')
            notes = Note.query.all()
            return render_template('.notes.html', notes=notes)
        except: 
            flash('There was a problem deleting note. Try again')
            notes = Note.query.all()
            return render_template('notes.html', notes=notes)
    else:
        flash("You don't have a permission to delete this note")
        notes = Note.query.all()
        return render_template('notes.html', notes=notes)

### Categories ###

### Display all categories ###

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

### Create new category ###

@app.route('/add_categories', methods=['GET', 'POST'])
@login_required
def add_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('categories'))
    else:
        flash('You need to login')
    return render_template('add_categories.html', form=form)

### Edit category ###

@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm()
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.add(category)
        db.session.commit()
        flash('The category has been updated')
        return redirect(url_for('.categories', id=category.id))
    form.name.data = category.name
    return render_template('edit_note.html', form=form)

### Delete category ###

@app.route('/categories/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_category(id):
    category_to_delete = Category.query.get_or_404(id)
    try:
        db.session.delete(category_to_delete)
        db.session.commit()
        flash('Category was deleted')
        categories = Category.query.all()
        return render_template('.categories.html', categories=categories)
    except: 
        flash('There was a problem deleting note. Try again')
        categories = Category.query.all()
        return render_template('categories.html', categories=categories)

### Search notes by the title ###

@app.route('/search', methods=['GET', 'POST'])
def search():
    q = request.args.get('q')
    if q:
        notes = Note.query.filter(Note.title.contains(q))
        return render_template('notes.html', notes=notes)
    else: 
        notes = Note.query.all()
        flash('No posts were found')
        return render_template(url_for('notes', notes=notes))

### Filter notes by category ###
    
@app.route('/categories/filter_category<int:id>', methods=['GET', 'POST'])
def filter_category(id):
    category = Category.query.get_or_404(id)
    if category.id:
        notes = Note.query.filter(Note.category_id == category.id)
        return render_template('notes.html', notes=notes)
    else:
        notes = Note.query.all()
        flash('No posts were found')
        return render_template(url_for('notes', notes=notes))