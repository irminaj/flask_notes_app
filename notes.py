import os

from flask import Flask, render_template, flash, url_for, redirect, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
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
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
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
    submit = SubmitField('Create')

# SearchForm, paziureti ar reikes, bet panasu, kad ne 

class SearchForm(FlaskForm):
    searched = StringField('Searched', validators=[DataRequired()])
    submit = SubmitField('Search')

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

note_category = db.Table('note_category', 
    db.Column('notes.id', db.Integer, db.ForeignKey('categories.id')),
    db.Column('categories.id', db.Integer, db.ForeignKey('notes.id'))
    )

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(500))
    content = db.Column(db.String(10000))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    categories = db.relationship('Category', secondary=note_category, backref='notes')

    def __repr__(self):
        return '<Note %r>' % self.name

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return '<Category %r>' % self.name

@app.route('/')
def index():
    return render_template('index.html')

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
                next = url_for('dashboard')
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    notes = Note.query.all()
    return render_template('notes.html', notes=notes)

@app.route('/add_note', methods=['GET', 'POST'])
@login_required
def add_note():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        flash('You need to login')
    return render_template('add_note.html', form=form)

@app.route('/notes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    note = Note.query.get_or_404(id)
    form = NoteForm()
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        db.session.add(note)
        db.session.commit()
        flash('The note has been updated')
        return redirect(url_for('.notes', id=note.id))
    if current_user.id == note.user_id:
        form.title.data = note.title
        form.content.data = note.content
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
            return render_template('notes.html', notes=notes)
        except: 
            flash('There was a problem deleting note. Try again')
            notes = Note.query.all()
            return render_template('notes.html', notes=notes)
    else:
        flash("You don't have a permission to delete this note")
        notes = Note.query.all()
        return render_template('notes.html', notes=notes)

### Search options ###

# @app.context_processor
# def base():
#     form = SearchForm()
#     return dict(form=form)

# @app.route('/search', methods=['POST', 'GET'])
# def search():
#     form = SearchForm()
#     notes = Note.query
#     if form.validate_on_submit():
#         notes.searched = form.searched.data
#         notes = notes.filter(Note.title.like('%' + notes.searched + '%'))
#         notes = notes.order_by(Note.title).all()
#         return render_template('search.html', form=form, searched = notes.searched, notes=notes)
#     else:
#         flash('No mathces were found')
#         notes = Note.query.all()
#         return render_template('notes.html', notes=notes)

# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     searched = request.args.get('searched')
#     if searched:
#         notes = Note.query.filter(Note.title.contains(searched))
#     else:
#         notes = Note.query.all()
#     return render_template('notes.html', notes=notes)

# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     form=SearchForm()
#     if request.method == 'POST' and form.validate_on_submit():
#         return redirect((url_for('search', query=form.search.data)))
#     return render_template('notes.html')

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
