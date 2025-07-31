import os
import re
from datetime import datetime

from flask import redirect, render_template, request, session, url_for, flash # Adding flash for displaying error and success messages
from flask_bcrypt import Bcrypt

from internlinkApp import app, db

flask_bcrypt = Bcrypt(app)

DEFAULT_USER_ROLE = 'student'

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_RESUME_EXTENSIONS = {'pdf'}

def allowed_file(filename, allowed_extensions):
    # his is a function which will help to check if the filename has an allowed file extension.
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def user_home_url():
    #It will help in generating a URL to the homepage for the users who are currently logged in.
    if 'loggedin' in session:
        role = session.get('role', None)
        # Checking the user role type and redirecting them to their specific role end points
        if role=='student': home_endpoint='student_home'
        elif role=='employer': home_endpoint='employer_home'
        elif role=='admin': home_endpoint='admin_home'
        else: home_endpoint = 'logout'
    else:
        home_endpoint = 'login'
    return url_for(home_endpoint)

# User Homepage Route
@app.route('/')
def root():
    return redirect(user_home_url())

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
         return redirect(user_home_url())

    username_invalid = False
    password_invalid = False
    account_inactive = False
    error_message = None 

    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error_message="username and password are missing."
            return render_template('login.html', username=username, error_message=error_message)

        with db.get_cursor() as cursor:
            cursor.execute('''
                       SELECT user_id, username, password_hash, role, status
                       FROM users
                       WHERE username = %s;
                       ''', (username,))
            account = cursor.fetchone()

            if account is not None:
                # Here we're checking if the user account is inactive
                if account['status'] == 'inactive':
                    account_inactive = True
                    return render_template('login.html', username=username, account_inactive=account_inactive)

                password_hash = account['password_hash']

                if flask_bcrypt.check_password_hash(password_hash, password):
                    session['loggedin'] = True
                    session['user_id'] = account['user_id']
                    session['username'] = account['username']
                    session['role'] = account['role']
                    return redirect(user_home_url())
                else:
                    password_invalid = True
                    return render_template('login.html', username=username, password_invalid=password_invalid)
            else:
                username_invalid = True
                return render_template('login.html', username=username, username_invalid=username_invalid)

    return render_template('login.html') # If the request is GET then render login template

# SignUp Route
@app.route('/signup', methods=['GET','POST'])
def signup():

    if 'loggedin' in session:
         return redirect(user_home_url())

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    full_name = request.form.get('full_name')
    university = request.form.get('university')
    course = request.form.get('course')
    resume_file = request.files.get('resume')

    username_error = None
    email_error = None
    password_error = None
    signup_successful = False
    error_message = None

    if request.method == 'POST':
        with db.get_cursor() as cursor:
            cursor.execute('SELECT user_id FROM users WHERE username = %s;', (username,))
            account_already_exists = cursor.fetchone() is not None

        if account_already_exists:
            username_error = 'An account already exists with this username.'
        elif len(username) > 50:
            username_error = 'Your username cannot exceed 50 characters.'
        elif not re.match(r'[A-Za-z0-9]+', username):
            username_error = 'Your username can only contain letters and numbers.'            

        if len(email) > 100:
            email_error = 'Your email address cannot exceed 100 characters.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            email_error = 'Invalid email address.'

        if len(password) < 8:
            password_error = 'Please choose a longer password!'
        elif not re.search(r'[A-Z]', password):
            password_error = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', password):
            password_error = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'[0-9]', password):
            password_error = 'Password must contain at least one digit.'
        elif not re.search(r'[^A-Za-z0-9]', password):
            password_error = 'Password must contain at least one special character.'

        if (username_error or email_error or password_error):
            return render_template('signup.html', username=username, email=email,
                                   username_error=username_error, email_error=email_error,
                                   password_error=password_error)
        else:
            password_hash = flask_bcrypt.generate_password_hash(password)

            try:
                with db.get_cursor() as cursor:
                    cursor.execute('''
                                INSERT INTO users (username, password_hash, email, role, status)
                                VALUES (%s, %s, %s, %s, %s);
                                ''',
                                (username, password_hash, email, DEFAULT_USER_ROLE, 'active'))
                signup_successful = True
                return render_template('signup.html', signup_successful=signup_successful)
            except Exception as e:
                print(f"Error during signup: {e}")
                error_message = "An error occurred during registration. Please try again."
                return render_template('signup.html', username=username, email=email, error_message=error_message)

    return render_template('signup.html')

# Profile Route
@app.route('/profile', methods=['GET'])
def profile():
    # If the user is not logged in then redirect to login page
    if 'loggedin' not in session:
         return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    with db.get_cursor() as cursor:
        # If the user role is student
        if role == 'student':
            cursor.execute('''
                            SELECT u.username, u.email, u.full_name, u.profile_image, u.role, u.status,
                                   s.university, s.course, s.resume_path
                            FROM users u
                            LEFT JOIN student s ON u.user_id = s.user_id
                            WHERE u.user_id = %s;
                            ''', (user_id,))
        # If the user role is employer
        elif role == 'employer':
            cursor.execute('''
                            SELECT u.username, u.email, u.full_name, u.profile_image, u.role, u.status,
                                   e.company_name, e.company_description, e.website, e.logo_path
                            FROM users u
                            LEFT JOIN employer e ON u.user_id = e.user_id
                            WHERE u.user_id = %s;
                            ''', (user_id,))
        # If the user role is admin
        elif role == 'admin':
            cursor.execute('SELECT username, email, full_name, profile_image, role, status FROM users WHERE user_id = %s;',
                           (user_id,))
        profile_data = cursor.fetchone()

    return render_template('profile.html', profile=profile_data)

# Change Password Route
@app.route('/change_password', methods=['GET'])
def change_password():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    return render_template('change_password.html')

# Log out Route
@app.route('/logout')
def logout():

    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", 'info') # Flashing message for user logging out
    return redirect(url_for('login'))