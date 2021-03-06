from flask import Flask, render_template, url_for, redirect, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_ckeditor import CKEditor
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

app = Flask(__name__, static_url_path='/static')
ckeditor = CKEditor(app)
app.secret_key = "thisisakey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.sqlite3'
app.config['SQLALCHEMY_BINDS'] = {
	'user' : 'sqlite:///users.sqlite3'
}
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.permanent_session_lifetime = timedelta(days=7)
db = SQLAlchemy(app)
admin = Admin(app)


class Post(db.Model):
	id = db.Column('id',db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	author = db.Column(db.String(100), nullable=False)
	body = db.Column(db.String(500), nullable=False)
	select = db.Column(db.String(500), nullable=False)
	author_s = db.Column(db.String(500), nullable=False)

	def __init__(self, title, author, body, select, author_s):
		self.title = title
		self.author = author
		self.body = body
		self.select = select
		self.author_s = author_s

class User(db.Model):
	__bind_key__ = 'user'
	id = db.Column('id',db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False)
	email = db.Column(db.String, nullable=False)
	password = db.Column(db.String, nullable=False)

	def __init__(self, name, email, password):
		self.name = name
		self.email = email
		self.password = password

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Post, db.session))
@app.route('/')
def home():
    return render_template('home.html', title='Home Page', posts=Post.query.filter_by(select=1))

@app.route('/adminlogin')
def hello(name=None):
    return render_template('adminlogin.html', name=name)
    
@app.route('/view')
def view():
	return render_template('view.html', values=User.query.all())

@app.route('/yourpost')
def yourpost():
	if 'name' in session:
		posts = Post.query.filter_by(author=session['name'])
		return render_template('yourposts.html', title='Your posts', posts=posts)
	else:
		flash('You must be logged in')
		return redirect(url_for('signup'))
	    
@app.route('/sharedpost')
def sharedpost():
	if 'name' in session:
		posts = Post.query.filter_by(author_s=session['name'])
		return render_template('sharedpost.html', title='Shared posts', posts=posts)
	else:
		flash('You must be logged in')
		return redirect(url_for('signup'))
	    	

@app.route('/signup', methods=['POST','GET'])
def signup():
	if request.method == "POST":
		session.permanent = True
		name = request.form["name"]
		email = request.form["email"]
		password = request.form["password"]
		found_user = User.query.filter_by(email=email).first()
		if not found_user:
			user = User(name,email,password)
			db.session.add(user)
			db.session.commit()
			session["name"] = name
			session["email"] = email
			session["password"] = password
			flash('Signed up.')
			return redirect(url_for("home"))
		else:
			flash('Email already in use.')
			return redirect(url_for("home"))
	else :
		if "name" in session:
			flash('Already logged in...')
			return redirect(url_for("home"))
		return render_template("signup.html", title="Sign Up")

@app.route('/signin', methods=['POST','GET'])
def signin():
	if request.method == "POST":
		session.permanent = True
		email = request.form["email"]
		password = request.form["password"]
		found_user = User.query.filter_by(email=email).first()
		if found_user:
			if password == found_user.password:
				session["name"] = found_user.name
				session["email"] = email
				session["password"] = password
				flash('Signed in.')
				return redirect(url_for("home"))
			else:
				flash('Wrong password')
				return render_template("signin.html", title="Sign Up")
			
		else:
			flash('User doesn\'t exists')
			return render_template("signin.html", title="Sign Up")
	else :
		if "name" in session:
			return redirect(url_for("home"))
		return render_template("signin.html", title="Sign In")

@app.route('/read/<title>')
def read(title):
	query = title.replace('?',' ')
	query = query.replace('/', ' ')
	post = Post.query.filter_by(title=query).first()
	if post:
		return render_template('read.html', title=title, post=post)
	else:
		return render_template('read.html', title='Error 404!', post='Not found')

@app.route('/write', methods=['POST','GET'])
def write():
	if request.method == "POST":
		title = request.form['title'] if 'title' in request.form else None
		body = request.form['body'] if 'body' in request.form else None
		select = request.form['select'] if 'select' in request.form else None
		author_s = request.form['author_s'] if 'author_s' in request.form else None
		if 'title' in request.form and 'body' in request.form:
			t = title.replace('?',' ')
			t = t.replace('/', ' ')
			search_result = Post.query.filter_by(title=t).first()
			if not search_result:
				post = Post(title=t,author=session['name'],body=body,select=select,author_s=author_s)
				db.session.add(post)
				db.session.commit()
				flash('Post saved')
				return redirect(url_for('read', title=t))
			else:
				flash('Cant save post')
			return render_template('write.html', title='Write A Post')
		else:
			flash('Fill every detail')
			return render_template('write.html', title='Write A Post')
		
	else:
		if "name" in session:
			return render_template('write.html', title='Write A Post')
		else:
			flash('You must be logged in')
			return redirect(url_for('signin'))
	
@app.route("/logout")
def logout():
	session.pop("name", None)
	session.pop("email", None)
	session.pop("password", None)
	return redirect(url_for("signin"))

if __name__ == '__main__':
	# posts = Post.query.all()
	# for post in posts:
	# 	db.session.delete(post)
	# users = User.query.all()
	# for user in users:
	# 	db.session.delete(post)
	db.session.commit()
	app.run()
	
