from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'healthops_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patient.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Patient Table
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    disease = db.Column(db.String(200))

# Create Database
with app.app_context():
    db.create_all()

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Add Patient
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        disease = request.form['disease']

        patient = Patient(name=name, age=age, disease=disease)

        db.session.add(patient)
        db.session.commit()
        
        flash('Patient added successfully.', 'success')
        return redirect(url_for('view_patients'))

    return render_template('add_patient.html')

# View Patients
@app.route('/patients')
@login_required
def view_patients():
    patients = Patient.query.all()
    return render_template('view_patients.html', patients=patients)

# Update Patient
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_patient(id):
    patient = Patient.query.get(id)

    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.disease = request.form['disease']

        db.session.commit()
        flash('Patient updated successfully.', 'success')
        return redirect(url_for('view_patients'))

    return render_template('update_patient.html', patient=patient)

# Delete Patient
@app.route('/delete/<int:id>')
@login_required
def delete_patient(id):
    patient = Patient.query.get(id)

    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully.', 'success')

    return redirect(url_for('view_patients'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)